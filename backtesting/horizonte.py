"""H11 — Avaliacao de estrategias em horizonte temporal superior.

TESE

Liu & Tsyvinski (2021) documentam momentum de serie temporal em criptoativos em
horizontes de UMA A QUATRO SEMANAS. O bot opera em 4 horas. Se o efeito existe
nessa escala e nao na atual, as nove hipoteses direcionais ja reprovadas mediram
a escala, nao a estrategia -- e a investigacao inteira precisa ser relida.

O QUE ESTE MODULO NAO FAZ

Nao simula. Nao julga. Nao define criterio. Ele orquestra estrategia x horizonte
x par e delega inteiramente: `engine.run_backtest` simula, `approval.
evaluate_approval` julga, `validation.split_train_validation` confirma fora da
amostra, `cross_sectional.walk_forward` divide em janelas. Introduzir criterio
proprio aqui tornaria o resultado incomparavel com as hipoteses ja registradas
em docs/research/registro-de-hipoteses.md.

O TRABALHO REAL E DECLARAR LIMITACAO DE AMOSTRA

Medicao previa (2026-09-01, 12 pares, requisicao de 2000 candles):

    4h  obtido 2000  uteis 1950  cobertura  333d  aquecimento   8d
    1d  obtido 2000  uteis 1950  cobertura 2000d  aquecimento  50d
    1w  obtido 311-473  uteis 261-423  cobertura ~2900d  aquecimento 350d

Em 1w, o split 70/30 produz janela de validacao de 78 a 127 candles, abaixo de
MIN_WINDOW_CANDLES=150. NENHUM par comporta a etapa de confirmacao fora da
amostra em escala semanal. O resultado correto e INCONCLUSIVO, nao reprovado --
ausencia de amostra nao e evidencia de ausencia de vantagem. Foi essa distincao
que separou H10 de uma reprovacao indevida.

Corolario registrado antes da execucao: se este modulo produzir 1w como
`confirmado` ou `reprovado`, o dimensionamento das janelas esta errado. Nao e
achado, e defeito.

RESTRICAO OPERACIONAL

Nao altera TIMEFRAME de producao (FR-012). O modulo le a configuracao apenas
para exibir a linha de base; nunca escreve em .env nem em estado do bot.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from backtesting.approval import evaluate_approval
from backtesting.cross_sectional import WalkForwardFold
from backtesting.engine import BacktestResult, simulate_backtest
from backtesting.validation import MIN_WINDOW_CANDLES
from config.settings import EDGE_MIN_TRADES, EMA_TREND, RSI_PERIOD
from data.fetcher import fetch_ohlcv
from strategy.base import BaseStrategy
from utils.logger import get_logger

log = get_logger("horizonte")

# Candles por dia em cada horizonte, para converter aquecimento e cobertura em
# tempo real. Sem isso, "50 candles de aquecimento" esconde que em escala
# semanal isso e quase um ano.
DIAS_POR_CANDLE = {
    "1h": 1 / 24,
    "4h": 4 / 24,
    "1d": 1.0,
    "1w": 7.0,
}

# Fracao abaixo da mediana do horizonte a partir da qual um par e marcado como
# historico curto. NAO se compara com o valor solicitado: 2000 candles semanais
# sao 38 anos, e a Binance nao existe ha tanto tempo -- a comparacao ingenua
# marcava os 12 pares em 1w, e alerta que dispara sempre equivale a alerta
# nenhum.
LIMIAR_HISTORICO_CURTO = 0.80

# Numero maximo de janelas de walk-forward, e minimo exigido pela etapa E4 da
# bateria. Abaixo de MIN_JANELAS_E4 o resultado e inconclusivo: tres janelas e o
# piso para distinguir vantagem de sorte de regime, e foi por ter olhado UMA
# janela que H7 quase foi aprovada com +29pp que nao replicou.
MAX_JANELAS = 5
MIN_JANELAS_E4 = 3


@dataclass
class DisponibilidadeHistorico:
    """Quanto a fonte de dados efetivamente entregou, por par e horizonte."""

    par: str
    horizonte: str
    solicitado: int
    obtido: int
    aquecimento: int
    dias_cobertos: float = 0.0
    historico_curto: bool = False
    erro: Optional[str] = None

    @property
    def utilizaveis(self) -> int:
        """Candles que sobram para sinal depois do aquecimento.

        Satura em zero: um par de listagem recente em escala semanal pode ter
        menos historico que o proprio aquecimento, e devolver negativo aqui
        propagaria numero invalido para o dimensionamento das janelas.
        """
        return max(0, self.obtido - self.aquecimento)

    @property
    def lacuna(self) -> int:
        """Diferenca entre o pedido e o recebido (FR-009).

        Pedir 2000 e receber 400 e normal em escala semanal. O que nao pode e
        passar silencioso: sem este numero, uma comparacao entre horizontes
        ficaria desbalanceada sem ninguem notar.
        """
        return max(0, self.solicitado - self.obtido)


def aquecimento_candles() -> int:
    """Candles consumidos antes do primeiro sinal possivel.

    Domina a EMA de tendencia; ADX(14) e RSI(14) cabem dentro dela. Derivado da
    configuracao em vez de constante literal, para que mudar EMA_TREND nao
    invalide silenciosamente o dimensionamento das janelas.
    """
    return max(EMA_TREND, RSI_PERIOD * 2)


def aquecimento_dias(horizonte: str) -> float:
    """O mesmo aquecimento expresso em tempo real (FR-010).

    50 candles em escala semanal sao 350 dias -- quase um ano antes do primeiro
    sinal. Declarado apenas em candles, o fato fica invisivel.
    """
    return aquecimento_candles() * DIAS_POR_CANDLE.get(horizonte, 1.0)


def medir_disponibilidade(
    pares: List[str], horizonte: str, solicitado: int = 2000,
) -> List[DisponibilidadeHistorico]:
    """Quanto cada par entrega neste horizonte, medido e nao presumido.

    Falha de um par vira registro de erro e NAO interrompe os demais (R7): uma
    varredura de 144 combinacoes que morre na terceira e inutil. Erro e
    distinguivel de "avaliado e nao operou" -- confundir os dois faria um par
    inacessivel parecer uma estrategia inerte.
    """
    aquec = aquecimento_candles()
    dias_por = DIAS_POR_CANDLE.get(horizonte, 1.0)
    medidas: List[DisponibilidadeHistorico] = []

    for par in pares:
        try:
            df = fetch_ohlcv(par, horizonte, solicitado)
            obtido = 0 if df is None or len(df) == 0 else len(df)
            medidas.append(DisponibilidadeHistorico(
                par=par, horizonte=horizonte, solicitado=solicitado,
                obtido=obtido, aquecimento=aquec,
                dias_cobertos=round(obtido * dias_por, 1),
            ))
        except Exception as exc:
            log.warning(f"{par} em {horizonte}: {type(exc).__name__}")
            medidas.append(DisponibilidadeHistorico(
                par=par, horizonte=horizonte, solicitado=solicitado,
                obtido=0, aquecimento=aquec, dias_cobertos=0.0,
                erro=f"{type(exc).__name__}: {str(exc)[:80]}",
            ))

    return medidas


def marcar_historico_curto(
    disponibilidades: List[DisponibilidadeHistorico],
) -> List[DisponibilidadeHistorico]:
    raise NotImplementedError("T029")


# ----------------------------------------------------------- avaliacao (US1)

@dataclass
class CombinacaoAvaliada:
    """Uma estrategia, em um horizonte, sobre um par."""

    estrategia: str
    horizonte: str
    par: str
    disponibilidade: DisponibilidadeHistorico
    resultado_janela_unica: Optional[BacktestResult] = None
    resultado_busca: Optional[BacktestResult] = None
    resultado_confirmacao: Optional[BacktestResult] = None
    folds: List[WalkForwardFold] = field(default_factory=list)
    retorno_sem_custo_pct: Optional[float] = None
    n_janelas: int = 0
    status: str = "inconclusivo"
    motivo: str = ""


def derivar_n_janelas(utilizaveis: int) -> int:
    """Quantas janelas de walk-forward o historico comporta (D2).

    Nao e numero fixo: cinco janelas contiguas sobre poucos candles semanais
    produzem fatias sem operacao alguma -- aconteceu em H10, onde a janela 1
    teve zero trades. O piso de MIN_WINDOW_CANDLES por fatia e o mesmo ja usado
    pela confirmacao fora da amostra, para as duas etapas nao discordarem sobre
    o que e amostra suficiente.
    """
    return min(MAX_JANELAS, utilizaveis // MIN_WINDOW_CANDLES)


def classificar_status(
    resultado: Optional[BacktestResult],
    confirmacao: Optional[BacktestResult],
    n_janelas: int,
    utilizaveis: int,
) -> Tuple[str, str]:
    """Veredito consolidado. `inconclusivo` PRECEDE `reprovado` (R1, FR-003).

    A ordem das checagens e o conteudo da regra: amostra insuficiente decide o
    status ANTES de qualquer avaliacao de metrica. Inverter a ordem faria uma
    combinacao com 3 operacoes e profit factor 0,2 ser reportada como reprovada,
    quando o que houve foi ausencia de amostra -- e ausencia de amostra nao e
    evidencia de ausencia de vantagem.
    """
    if resultado is None:
        return "inconclusivo", "sem resultado de simulacao"

    if resultado.total_trades < EDGE_MIN_TRADES:
        return ("inconclusivo",
                f"{resultado.total_trades} operacoes, abaixo do minimo de {EDGE_MIN_TRADES}")

    # A janela de descoberta e avaliada ANTES de exigir confirmacao: se a
    # estrategia ja reprova onde foi descoberta, nao ha o que confirmar. A
    # janela de confirmacao so pode REBAIXAR um resultado, nunca promove-lo.
    veredito_busca = evaluate_approval(resultado)
    if veredito_busca.status != "aprovado":
        return "reprovado", "; ".join(veredito_busca.reasons[:3])

    if confirmacao is None:
        return ("inconclusivo",
                f"amostra nao comporta janela de confirmacao "
                f"({utilizaveis} candles uteis, minimo {MIN_WINDOW_CANDLES} por fatia)")

    if n_janelas < MIN_JANELAS_E4:
        return ("inconclusivo",
                f"{n_janelas} janelas de walk-forward, abaixo do minimo de {MIN_JANELAS_E4}")

    veredito_conf = evaluate_approval(confirmacao)
    if veredito_conf.status != "aprovado":
        # Aprovada onde foi descoberta e nao sustentada fora. NAO e aprovacao.
        return "so_na_busca", "; ".join(veredito_conf.reasons[:3])

    return "confirmado", "aprovado na busca e na confirmacao"


def _simular(df, estrategia: BaseStrategy, **kwargs) -> Optional[BacktestResult]:
    """Simula sobre um DataFrame ja obtido, para nao rebuscar a mesma serie.

    `run_backtest` busca dados por conta propria; aqui a serie ja esta em maos e
    precisa ser fatiada em busca/confirmacao, entao o caminho e `simulate_backtest`.
    """
    if df is None or len(df) < aquecimento_candles() + 10:
        return None
    try:
        preparado = estrategia.calculate_indicators(df.copy())
        return simulate_backtest(
            preparado, estrategia, start_index=aquecimento_candles(), **kwargs
        )
    except Exception as exc:
        log.warning(f"simulacao falhou: {type(exc).__name__}: {str(exc)[:60]}")
        return None
