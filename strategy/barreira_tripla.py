"""H14 -- rotulagem por barreira tripla e atributos declarados (spec 027).

TESE

Rotular cada evento pela barreira que o preco toca primeiro -- alvo, stop, ou
limite de tempo -- transforma a previsao de direcao num problema de
classificacao com rotulos ECONOMICAMENTE SIGNIFICATIVOS, em vez de "o preco sobe
no proximo candle?".

O LIMIAR DE SUCESSO ESTA DECLARADO E FOI MEDIDO ANTES DO TESTE

Com as barreiras que o proprio bot usa (stop 1,5xATR, alvo 3,0xATR, limite de
24 velas), sobre 23.412 eventos dos 12 pares do universo:

    alvo 23,4% | stop 62,8% | tempo 12,8%

Uma entrada em instante ALEATORIO tem expectativa

    E = 0,234 x 3,0 - 0,628 x 1,5 = -0,241 ATR

NEGATIVA. O stop esta a metade da distancia do alvo e e tocado 2,7 vezes mais.
Disso sai o criterio que o classificador precisa vencer:

    razao de chances alvo/stop observada   0,372
    razao necessaria para empatar          0,500
    elevacao relativa exigida do modelo    +34,3%

E criterio interno a decisao, que nao depende do regime do periodo -- melhor que
"superar buy-and-hold". Registrado antes da execucao para nao poder ser
reinterpretado depois.

ACURACIA NAO E A METRICA

Prever sempre "stop" acerta 62,8% e nunca opera. A grandeza que importa e a
razao de chances no SUBCONJUNTO em que o modelo decide entrar. Um classificador
que nao eleve essa razao acima de 0,500 nao pode ser lucrativo com estas
barreiras, por mais alta que seja sua acuracia.

ROTULO BINARIO PORQUE O BOT SO OPERA COMPRADO

A decisao real e "entrar agora?", cuja resposta util e a probabilidade de o alvo
vir antes do stop. `stop` e `tempo` colapsam na classe negativa; `rotulo_bruto`
preserva as tres para o relatorio poder exibir o desbalanceamento.
"""
from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd

from config.settings import ATR_SL_MULTIPLIER, ATR_TP_MULTIPLIER
from utils.logger import get_logger

log = get_logger("barreira_tripla")

LIMITE_VELAS_PADRAO = 24  # 4 dias em 4h; horizonte mediano medido: 8 velas

# Conjunto DECLARADO (FR-003). Selecionado por independencia, em ordem de
# distincao conceitual -- liquidez, volatilidade, forca de tendencia, posicao,
# momento -- com limiar de correlacao 0,80. NENHUMA metrica de acerto participou
# da selecao; consultar desempenho aqui seria busca de atributos.
#
# Descartados, com a correlacao medida contra `dist_ema_slow`:
#   dist_ema_fast 0,959 | dist_ema_trend 0,908 | rsi 0,901 | pos_bb 0,807
# Correlacao de 0,96 desestabiliza a estimacao de maxima verossimilhanca: os
# coeficientes ficam mal determinados e o modelo pode nao convergir.
ATRIBUTOS = ["volume_ratio", "atr_ratio", "adx", "dist_ema_slow", "macd"]


@dataclass
class ParametrosBarreira:
    """Reusa os multiplicadores do bot. Nao introduz parametro novo de risco."""

    sl_mult: float = ATR_SL_MULTIPLIER
    tp_mult: float = ATR_TP_MULTIPLIER
    limite_velas: int = LIMITE_VELAS_PADRAO

    @property
    def razao_de_empate(self) -> float:
        """Razao de chances alvo/stop que zera a expectativa.

        Com stop a `sl_mult` e alvo a `tp_mult`, o ponto de equilibrio e
        `p_alvo x tp_mult = p_stop x sl_mult`, isto e, `p_alvo/p_stop =
        sl_mult/tp_mult`. Nos valores do bot: 1,5/3,0 = 0,500.
        """
        return self.sl_mult / self.tp_mult


def rotular(df: pd.DataFrame, params: Optional[ParametrosBarreira] = None) -> pd.DataFrame:
    """Rotula cada vela pela barreira tocada primeiro.

    CAUSAL: para o evento em `i`, olha apenas as velas `i+1 .. i+limite`. Nada
    anterior a `i` participa, e nada alem do limite conta.

    Devolve tambem `fim_horizonte` -- o instante em que a barreira foi tocada,
    ou o limite de tempo. E o campo que TORNA A PURGA POSSIVEL: sem ele nao ha
    como saber quais amostras de treino se sobrepoem a janela de teste.
    """
    p = params or ParametrosBarreira()
    if "atr" not in df.columns:
        raise ValueError("rotulagem exige a coluna 'atr'")

    close = df["close"].to_numpy(dtype=float)
    high = df["high"].to_numpy(dtype=float)
    low = df["low"].to_numpy(dtype=float)
    atr = df["atr"].to_numpy(dtype=float)
    n = len(df)

    bruto = np.full(n, np.nan)
    fim_pos = np.arange(n)

    for i in range(n):
        a = atr[i]
        if not np.isfinite(a) or a <= 0:
            # ATR invalido nao permite definir barreira. Rotular assim mesmo
            # produziria um rotulo arbitrario com aparencia de dado.
            continue

        alvo = close[i] + p.tp_mult * a
        stop = close[i] - p.sl_mult * a
        limite = min(i + p.limite_velas, n - 1)

        r, fim = 0, limite
        for j in range(i + 1, limite + 1):
            tocou_stop = low[j] <= stop
            tocou_alvo = high[j] >= alvo
            if tocou_stop:
                # Precedencia do stop quando a mesma vela toca as duas: com OHLC
                # agregado nao da para saber qual veio primeiro, e assumir o
                # alvo produziria rotulos otimistas por construcao.
                r, fim = -1, j
                break
            if tocou_alvo:
                r, fim = 1, j
                break
        bruto[i] = r
        fim_pos[i] = fim

    return pd.DataFrame({
        "instante": df.index,
        "rotulo_bruto": bruto,
        "rotulo": np.where(bruto == 1, 1.0, np.where(np.isnan(bruto), np.nan, 0.0)),
        "fim_horizonte": df.index[fim_pos],
    }, index=df.index)


def extrair_atributos(df: pd.DataFrame) -> pd.DataFrame:
    """Os cinco atributos declarados, todos adimensionais ou normalizados.

    A normalizacao pelo preco e pre-condicao para agrupar pares (D4): dois pares
    com o mesmo comportamento e precos 100x distintos precisam produzir os
    mesmos atributos, senao o modelo aprenderia a escala do par.
    """
    c = df["close"]
    x = pd.DataFrame(index=df.index)
    x["volume_ratio"] = df["volume"] / df["volume_ma"].replace(0, np.nan)
    x["atr_ratio"] = df["atr_ratio"]
    x["adx"] = df["adx"]
    x["dist_ema_slow"] = (c - df["ema_slow"]) / c
    x["macd"] = df["macd"] / c
    return x[ATRIBUTOS]


def distribuicao_classes(rotulo_bruto) -> dict:
    """Frequencia das tres classes, em pontos percentuais.

    Exibida no relatorio porque e o que revela desbalanceamento -- e o
    desbalanceamento e o que torna a acuracia enganosa.
    """
    s = pd.Series(rotulo_bruto).dropna()
    if len(s) == 0:
        return {"alvo": 0.0, "stop": 0.0, "tempo": 0.0, "n": 0}
    return {
        "alvo": float((s == 1).mean() * 100),
        "stop": float((s == -1).mean() * 100),
        "tempo": float((s == 0).mean() * 100),
        "n": int(len(s)),
    }


def razao_de_chances(rotulo_bruto) -> Optional[float]:
    """Alvo sobre stop. `None` se nao ha amostra; infinito se nao ha stop.

    Devolver 0,0 na ausencia de stop leria o melhor caso possivel como o pior.
    """
    s = pd.Series(rotulo_bruto).dropna()
    if len(s) == 0:
        return None
    stops = int((s == -1).sum())
    if stops == 0:
        return float("inf")
    return float((s == 1).sum()) / stops
