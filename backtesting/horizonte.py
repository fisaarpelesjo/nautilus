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
import statistics
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from backtesting.approval import evaluate_approval
from backtesting.cross_sectional import WalkForwardFold
from backtesting.engine import BacktestResult, precompute_signals, simulate_backtest
from backtesting.validation import MIN_WINDOW_CANDLES, split_train_validation
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
    """Marca pares com historico curto RELATIVO A MEDIANA DO HORIZONTE (D3).

    Nao se compara com o valor solicitado: 2000 candles semanais sao 38 anos, e
    a Binance nao existe ha tanto tempo. A comparacao ingenua marcava os 12
    pares em escala semanal, e alerta que dispara sempre equivale a alerta
    nenhum -- o operador aprende a ignora-lo.

    Comparando com a mediana, sobram os pares de listagem genuinamente recente.
    """
    validos = [d.obtido for d in disponibilidades if not d.erro and d.obtido > 0]
    if not validos:
        return disponibilidades

    mediana = statistics.median(validos)
    piso = mediana * LIMIAR_HISTORICO_CURTO
    for d in disponibilidades:
        d.historico_curto = bool(not d.erro and 0 < d.obtido < piso)
    return disponibilidades



# ------------------------------------------------------------- escopo de H11

# Universo: os mesmos 12 pares usados na avaliacao de H7 (momentum transversal)
# e H9 (premio de rebalanceamento). A spec exige "o mesmo universo das
# avaliacoes anteriores, para que os resultados sejam comparaveis" -- usar
# `PAIRS` traria listagens recentes sem historico semanal algum, que nao
# aparecem nas hipoteses ja registradas.
UNIVERSO_H11 = [
    "BTC/USDT", "ETH/USDT", "SOL/USDT", "LINK/USDT", "BCH/USDT", "TRX/USDT",
    "XRP/USDT", "AVAX/USDT", "LTC/USDT", "DOT/USDT", "ADA/USDT", "ATOM/USDT",
]


def ESTRATEGIAS_H11():
    """As quatro estrategias no escopo da spec 024.

    NAO inclui os wrappers (DayFilterStrategy, NoSellExitStrategy): a spec lista
    nominalmente EmaRsi, Breakout, MeanReversion e SqueezeBreakout, e H11 mede a
    ESCALA TEMPORAL, nao o sinal. Wrapper e variacao de sinal.

    Custo medido da exclusao, serie de 2000 candles: DayFilterStrategy consome
    86,67 s por combinacao contra 0,27 s da EmaRsi que ela envolve -- e wrapper
    sem `.params`, cai no caminho por candle E rechama a estrategia base a cada
    vela. Incluir os 5 levaria a varredura de 31 para 159 minutos sem responder
    nada que a spec tenha perguntado.
    """
    from strategy.breakout import BreakoutStrategy
    from strategy.ema_rsi import EmaRsiStrategy
    from strategy.mean_reversion import MeanReversionStrategy
    from strategy.squeeze_breakout import SqueezeBreakoutStrategy

    return {
        "EMA/RSI": EmaRsiStrategy(),
        "Breakout 150": BreakoutStrategy(window=150),
        "Mean Reversion": MeanReversionStrategy(),
        "Squeeze Breakout": SqueezeBreakoutStrategy(),
    }


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

    # A mesma checagem de amostra da janela de busca, aplicada a de confirmacao.
    # `so_na_busca` afirma algo substantivo -- "passou onde foi descoberta e NAO
    # se sustentou fora". Com menos operacoes que o minimo, essa afirmacao nao
    # tem suporte: nao foi testada e reprovou, foi testada de menos.
    if confirmacao.total_trades < EDGE_MIN_TRADES:
        return ("inconclusivo",
                f"janela de confirmacao com {confirmacao.total_trades} operacoes, "
                f"abaixo do minimo de {EDGE_MIN_TRADES}")

    veredito_conf = evaluate_approval(confirmacao)
    if veredito_conf.status != "aprovado":
        # Aprovada onde foi descoberta e nao sustentada fora. NAO e aprovacao.
        return "so_na_busca", "; ".join(veredito_conf.reasons[:3])

    return "confirmado", "aprovado na busca e na confirmacao"


def preparar(df, estrategia: BaseStrategy):
    """Calcula indicadores UMA vez sobre a serie completa.

    Motivacao dupla, e a segunda importa mais que a primeira.

    DESEMPENHO: cada combinacao passa 9 vezes pela serie (janela unica, busca,
    confirmacao, N folds, execucao sem custo). Recalcular indicadores em cada
    passagem multiplica por 9 o custo de dados sobrepostos. Medido: a varredura
    de 345 combinacoes consumia 3 nucleos continuamente sem terminar em 11 min.

    CORRECAO: recalcular por fatia da a cada fold um aquecimento proprio,
    cegando-o para o historico anterior. Producao nunca opera assim -- o bot tem
    a serie inteira em maos. Indicadores do projeto (EMA, RSI, ADX, Bollinger,
    ATR) sao causais, usam apenas o passado, entao calcular no todo e fatiar
    entrega a cada fold exatamente a informacao que o bot ao vivo teria. Nao ha
    vazamento de futuro; ha remocao de uma descontinuidade artificial.
    """
    if df is None or len(df) == 0:
        return None
    try:
        return estrategia.calculate_indicators(df.copy())
    except Exception as exc:
        log.warning(f"indicadores falharam: {type(exc).__name__}: {str(exc)[:60]}")
        return None


def _simular(preparado, estrategia: BaseStrategy, **kwargs) -> Optional[BacktestResult]:
    """Simula sobre um DataFrame JA PREPARADO por `preparar()`.

    Recebe indicadores prontos de proposito: ver a docstring de `preparar` para
    por que recalcular por fatia e mais lento E menos correto.
    """
    if preparado is None or len(preparado) < aquecimento_candles() + 10:
        return None
    try:

        # Caminho vetorizado quando a estrategia o suporta. `precompute_signals`
        # exige `.params` (so EmaRsiStrategy expoe hoje); as demais caem no
        # caminho por candle. A diferenca nao e cosmetica: a varredura completa
        # sao 144 combinacoes x (janela unica + busca + confirmacao + N folds +
        # execucao sem custo), e o caminho por candle chama generate_signal uma
        # vez por vela em cada uma dessas passagens.
        sinais = None
        if hasattr(estrategia, "params"):
            try:
                sinais = precompute_signals(preparado, estrategia)
            except Exception:
                sinais = None

        return simulate_backtest(
            preparado, estrategia, start_index=aquecimento_candles(),
            precomputed_signals=sinais, **kwargs
        )
    except Exception as exc:
        log.warning(f"simulacao falhou: {type(exc).__name__}: {str(exc)[:60]}")
        return None


def _walk_forward_par(
    preparado, estrategia: BaseStrategy, n_janelas: int,
) -> List[WalkForwardFold]:
    """Walk-forward para backtest de PAR UNICO.

    `cross_sectional.walk_forward` opera sobre carteira e nao serve aqui. O que
    se reusa e o `WalkForwardFold` -- especificamente sua propriedade
    `ganho_de_timing_pp`, que desconta exposicao do retorno. Sem esse desconto,
    uma estrategia que fica em caixa durante queda parece habilidosa sem ser
    (achado M7).

    Janela sem operacao alguma e devolvida com trades=0 e o consumidor a exclui
    das agregacoes (R3, FR-006). Conta-la como neutra diluiria tanto resultado
    bom quanto ruim.
    """
    if n_janelas <= 0 or preparado is None or len(preparado) == 0:
        return []

    tam = len(preparado) // n_janelas
    if tam <= aquecimento_candles():
        return []

    folds: List[WalkForwardFold] = []
    for j in range(n_janelas):
        fatia = preparado.iloc[j * tam:(j + 1) * tam]
        r = _simular(fatia, estrategia)
        if r is None:
            folds.append(WalkForwardFold(
                janela=j + 1, buy_hold_pct=0.0, retorno_pct=0.0,
                exposicao_pct=0.0, max_drawdown_pct=0.0, trades=0,
            ))
            continue
        folds.append(WalkForwardFold(
            janela=j + 1,
            buy_hold_pct=r.buy_hold_return_pct,
            retorno_pct=r.total_return_pct,
            exposicao_pct=r.exposure_pct,
            max_drawdown_pct=r.max_drawdown_pct,
            trades=r.total_trades,
        ))
    return folds


def folds_uteis(folds: List[WalkForwardFold]) -> List[WalkForwardFold]:
    """Alias de folds_nao_vazios, nome curto para uso na exibicao."""
    return folds_nao_vazios(folds)


def folds_nao_vazios(folds: List[WalkForwardFold]) -> List[WalkForwardFold]:
    """Exclui janelas sem operacao (R3, FR-006)."""
    return [f for f in folds if f.trades > 0]


def _avaliar_combinacao(
    estrategia: BaseStrategy,
    nome_estrategia: str,
    horizonte: str,
    par: str,
    disponibilidade: DisponibilidadeHistorico,
    df=None,
) -> CombinacaoAvaliada:
    """Submete uma combinacao a E2, E3, E4 e E6, e consolida o veredito."""
    comb = CombinacaoAvaliada(
        estrategia=nome_estrategia, horizonte=horizonte, par=par,
        disponibilidade=disponibilidade,
    )

    if disponibilidade.erro:
        comb.status = "erro"
        comb.motivo = disponibilidade.erro
        return comb

    # Guard de aquecimento (T030, FR-010): se o aquecimento consome todo o
    # historico, nao ha janela de teste e nao adianta simular.
    if disponibilidade.utilizaveis <= 0:
        comb.status = "inconclusivo"
        comb.motivo = (f"aquecimento de {disponibilidade.aquecimento} candles "
                       f"excede o historico de {disponibilidade.obtido}")
        return comb

    if df is None:
        try:
            df = fetch_ohlcv(par, horizonte, disponibilidade.solicitado)
        except Exception as exc:
            comb.status = "erro"
            comb.motivo = f"{type(exc).__name__}: {str(exc)[:80]}"
            return comb

    # Indicadores UMA vez; todas as passagens fatiam o resultado preparado.
    preparado = preparar(df, estrategia)
    if preparado is None:
        comb.status = "erro"
        comb.motivo = "falha ao calcular indicadores"
        return comb

    # E2 -- janela unica
    comb.resultado_janela_unica = _simular(preparado, estrategia)

    # E3 -- confirmacao fora da amostra
    treino, validacao = split_train_validation(preparado)
    comb.resultado_busca = _simular(treino, estrategia)
    comb.resultado_confirmacao = _simular(validacao, estrategia) if validacao is not None else None

    # E4/E5 -- walk-forward com desconto de exposicao
    comb.n_janelas = derivar_n_janelas(disponibilidade.utilizaveis)
    comb.folds = _walk_forward_par(preparado, estrategia, comb.n_janelas)

    # E6 -- sensibilidade a custo
    sem_custo = _simular(preparado, estrategia, fee_rate=0.0, slippage_pct=0.0)
    comb.retorno_sem_custo_pct = sem_custo.total_return_pct if sem_custo else None

    comb.status, comb.motivo = classificar_status(
        resultado=comb.resultado_janela_unica,
        confirmacao=comb.resultado_confirmacao,
        n_janelas=comb.n_janelas,
        utilizaveis=disponibilidade.utilizaveis,
    )
    return comb


@dataclass
class RelatorioHorizonte:
    """Agregacao das combinacoes de um mesmo horizonte."""

    horizonte: str
    combinacoes: List[CombinacaoAvaliada] = field(default_factory=list)

    @property
    def n_avaliadas(self) -> int:
        return len(self.combinacoes)

    @property
    def n_confirmadas(self) -> int:
        return sum(1 for c in self.combinacoes if c.status == "confirmado")

    @property
    def n_inconclusivas(self) -> int:
        return sum(1 for c in self.combinacoes if c.status == "inconclusivo")

    @property
    def n_erros(self) -> int:
        return sum(1 for c in self.combinacoes if c.status == "erro")

    @property
    def candles_medianos(self) -> int:
        obtidos = [c.disponibilidade.obtido for c in self.combinacoes
                   if not c.disponibilidade.erro]
        if not obtidos:
            return 0
        return int(statistics.median(obtidos))

    @property
    def aquecimento_dias_horizonte(self) -> float:
        return aquecimento_dias(self.horizonte)

    def ordenadas(self) -> List[CombinacaoAvaliada]:
        """Confirmadas primeiro, depois so_na_busca, reprovadas, inconclusivas, erro."""
        ordem = {"confirmado": 0, "so_na_busca": 1, "reprovado": 2,
                 "inconclusivo": 3, "erro": 4}
        return sorted(self.combinacoes, key=lambda c: (ordem.get(c.status, 9), c.estrategia, c.par))


def run_horizonte_scan(
    estrategias: Dict[str, BaseStrategy],
    pares: List[str],
    horizontes: List[str],
    solicitado: int = 2000,
) -> List[RelatorioHorizonte]:
    """Varre estrategia x horizonte x par.

    Busca a serie UMA vez por par/horizonte e a reusa entre as estrategias: sem
    isso a varredura faria 4x mais chamadas de rede para os mesmos dados.

    Falha isolada nao aborta a varredura (R7).
    """
    relatorios: List[RelatorioHorizonte] = []

    for horizonte in horizontes:
        rel = RelatorioHorizonte(horizonte=horizonte)
        disponibilidades = marcar_historico_curto(
            medir_disponibilidade(pares, horizonte, solicitado)
        )

        for disp in disponibilidades:
            df = None
            if not disp.erro:
                try:
                    df = fetch_ohlcv(disp.par, horizonte, solicitado)
                except Exception as exc:
                    log.warning(f"{disp.par} {horizonte}: {type(exc).__name__}")

            for nome, estrategia in estrategias.items():
                try:
                    rel.combinacoes.append(_avaliar_combinacao(
                        estrategia, nome, horizonte, disp.par, disp, df=df,
                    ))
                except Exception as exc:
                    log.warning(f"{nome} x {disp.par} x {horizonte}: {type(exc).__name__}")
                    rel.combinacoes.append(CombinacaoAvaliada(
                        estrategia=nome, horizonte=horizonte, par=disp.par,
                        disponibilidade=disp, status="erro",
                        motivo=f"{type(exc).__name__}: {str(exc)[:80]}",
                    ))

        relatorios.append(rel)

    return relatorios
