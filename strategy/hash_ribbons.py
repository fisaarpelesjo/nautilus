"""H36 -- hash ribbons: capitulacao de mineradores (spec 073). Sinal de
entrada/saida experimental de PESQUISA, mesmo padrao de
`strategy/breakout.py`: nao e usado por `trading/runner.py` nem
`backtesting/engine.py::run_backtest` por omissao.

Cruzamento de medias moveis de 30/60 dias do hashrate de Bitcoin
(Charles Edwards/Capriole, 2019) -- mecanismo de OFERTA (economia de
mineracao), nao sinal de preco. Ver
`specs/073-h36-hash-ribbons/research.md` para D1-D2 declarados antes de
medir:

D1: cruzamento de alta (30d cruza acima de 60d, "recuperacao" apos
"capitulacao") = BUY; cruzamento de baixa simetrico = SELL. Medias
moveis SIMPLES, sem suavizacao adicional.

D2: sem SL/TP artificial -- o proprio indicador define entrada e saida;
o SL/TP/trailing por ATR ja generico de `simulate_backtest` permanece
ativo sem alteracao (mesmo comportamento que a producao teria).

Alinhamento causal D-1: candle do dia D usa o valor completo do dia D-1,
nunca o dia corrente (ainda incompleto na fonte) -- mesma disciplina de
H17/H32 (`backtesting.onchain_hipotese._merge_causal`). A logica e
reimplementada aqui (nao importada) para nao inverter a direcao de
dependencia do projeto: nenhum modulo de `strategy/` importa de
`backtesting/` hoje, e este arquivo nao deveria ser o primeiro a fazer
isso por uma funcao de ~10 linhas.
"""
import pandas as pd
import ta

from strategy.base import BaseStrategy, Signal, TradeSignal


def _alinhar_causal(indice_candles: pd.DatetimeIndex, serie_diaria: pd.Series) -> pd.Series:
    """Para um candle no dia D, usa o valor do dia D-1 completo -- nunca o
    dia corrente, ainda incompleto na fonte. Dia ausente leva adiante o
    ultimo conhecido, nunca interpola. Mesma logica de
    `backtesting.onchain_hipotese._merge_causal`."""
    indice_utc = indice_candles.tz_convert("UTC") if indice_candles.tz else indice_candles.tz_localize("UTC")
    serie_ordenada = serie_diaria.sort_index().dropna()

    valores = []
    for t in indice_utc:
        dia_disponivel = t.normalize() - pd.Timedelta(days=1)
        sub = serie_ordenada[serie_ordenada.index <= dia_disponivel]
        valores.append(sub.iloc[-1] if len(sub) else float("nan"))
    return pd.Series(valores, index=indice_candles)

JANELA_CURTA_DIAS = 30
JANELA_LONGA_DIAS = 60


class HashRibbonsStrategy(BaseStrategy):
    """BUY no cruzamento de alta das medias de 30/60 dias do hashrate,
    SELL no cruzamento de baixa simetrico. Recebe a serie diaria de
    hashrate ja buscada (nao busca dado por conta propria -- mesma
    responsabilidade de orquestracao ja seguida por
    `backtesting/crowding_extremo.py`, H35)."""

    def __init__(self, hashrate_diario: pd.Series):
        self.hashrate_diario = hashrate_diario.sort_index().dropna()

    def _cruzamentos_diarios(self) -> pd.DataFrame:
        ma_curta = self.hashrate_diario.rolling(JANELA_CURTA_DIAS).mean()
        ma_longa = self.hashrate_diario.rolling(JANELA_LONGA_DIAS).mean()
        cruzamento_alta = (ma_curta.shift(1) <= ma_longa.shift(1)) & (ma_curta > ma_longa)
        cruzamento_baixa = (ma_curta.shift(1) >= ma_longa.shift(1)) & (ma_curta < ma_longa)
        return pd.DataFrame({
            "cruzamento_alta": cruzamento_alta, "cruzamento_baixa": cruzamento_baixa,
        }, index=self.hashrate_diario.index)

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["atr"] = ta.volatility.AverageTrueRange(
            df["high"], df["low"], df["close"], window=14
        ).average_true_range()

        cruzamentos = self._cruzamentos_diarios()
        df["cruzamento_alta"] = _alinhar_causal(df.index, cruzamentos["cruzamento_alta"].astype(float)).fillna(0) > 0.5
        df["cruzamento_baixa"] = _alinhar_causal(df.index, cruzamentos["cruzamento_baixa"].astype(float)).fillna(0) > 0.5
        return df

    def generate_signal(self, df: pd.DataFrame) -> TradeSignal:
        if len(df) < 15:  # warmup minimo do ATR14 -- cruzamentos ja vem prontos do hashrate diario
            return TradeSignal(Signal.HOLD, df.iloc[-1]["close"] if len(df) else 0, "Dados insuficientes")

        df = self.calculate_indicators(df)
        curr = df.iloc[-1]
        price = curr["close"]

        if curr["cruzamento_alta"]:
            return TradeSignal(Signal.BUY, price, "Hash ribbons: cruzamento de alta (capitulacao -> recuperacao)")
        if curr["cruzamento_baixa"]:
            return TradeSignal(Signal.SELL, price, "Hash ribbons: cruzamento de baixa")
        return TradeSignal(Signal.HOLD, price, "Sem cruzamento de hashrate no dia")


def precompute_signals(candles: pd.DataFrame, hashrate_diario: pd.Series) -> pd.Series:
    """Sinal (BUY/SELL/HOLD) para TODOS os candles de uma vez, para uso como
    `precomputed_signals` de `simulate_backtest` (mesmo padrao de
    `backtesting.engine.precompute_signals` para `EmaRsiStrategy`).

    Necessario porque `_alinhar_causal` e um loop Python por candle (nao
    vetorizado) -- sem isso, `simulate_backtest` chamaria
    `generate_signal(df.iloc[:i])` a cada candle, e cada chamada
    recalcularia `calculate_indicators` (logo, `_alinhar_causal`) sobre a
    fatia crescente, virando O(n^2) (achado de code-review: ~18min so na
    janela unica com N_CANDLES=7000, antes desta correcao). O cruzamento
    diario e causal e nao depende de quantos candles totais existem, entao
    calcular uma vez sobre o indice inteiro e correto, nao uma aproximacao."""
    strategy = HashRibbonsStrategy(hashrate_diario)
    cruzamentos = strategy._cruzamentos_diarios()
    cruzamento_alta = _alinhar_causal(candles.index, cruzamentos["cruzamento_alta"].astype(float)).fillna(0) > 0.5
    cruzamento_baixa = _alinhar_causal(candles.index, cruzamentos["cruzamento_baixa"].astype(float)).fillna(0) > 0.5

    sinal = pd.Series(Signal.HOLD, index=candles.index)
    sinal[cruzamento_baixa] = Signal.SELL
    sinal[cruzamento_alta] = Signal.BUY
    return sinal
