"""H13 -- Barras dirigidas por informacao (spec 026).

TESE

Amostrar o mercado em intervalos de tempo fixos e uma escolha arbitraria, nao
uma propriedade do mercado. Informacao nao chega uniformemente no tempo: chega
em rajadas. Uma barra de 4h numa madrugada parada e uma barra de 4h durante uma
liquidacao em cascata carregam quantidades de informacao radicalmente
diferentes, e o backtest as trata como observacoes equivalentes.

Barras dirigidas por informacao fecham quando uma quantidade de ATIVIDADE se
acumula -- valor negociado ou desvio acumulado -- em vez de quando o relogio
marca.

MOTIVACAO VEM DE DENTRO DO REGISTRO

As doze hipoteses avaliadas rodaram TODAS sobre candles de tempo fixo. Se o
esquema de amostragem for o problema, cada hipotese direcional reprovada mediu a
AMOSTRAGEM, nao a estrategia.

O INDICE DA BARRA E O INSTANTE DE FECHAMENTO

Nao o de abertura. E o instante em que a barra passa a existir e em que uma
decisao poderia ser tomada sobre ela. Indexar pela abertura dataria a barra num
momento em que seu conteudo ainda era desconhecido -- vazamento de futuro por
convencao de indice.

CAUSALIDADE E A MAIOR FONTE DE FALSO POSITIVO DESTA SPEC

Uma barra fecha quando o acumulado cruza o limiar, e isso e conhecivel em tempo
real. Mas qualquer implementacao que use o total da barra para decidir onde ela
COMECA introduz futuro. M2 documenta exatamente essa classe de defeito passando
meses despercebida no projeto: um filtro que comparava preco historico contra
indicador corrente. Por isso a construcao aqui e um unico varrimento para a
frente, e existe teste de reconstrucao incremental provando igualdade exata.

PERDA DECLARADA EM RELACAO A DADOS DE NEGOCIACAO

Barras canonicas se constroem de ticks. O projeto consome candles agregados,
entao uma barra e sempre uniao de candles INTEIROS e suas fronteiras so caem em
marcas de hora. Com base 1h e mediana de 4 candles por barra (medido, D3), o
erro de posicionamento da fronteira e de ate +-0,5h numa barra de ~4h: cerca de
12% da largura tipica. E aproximacao, esta quantificada, e o veredito deve
dize-lo.
"""
from dataclasses import dataclass
from typing import List, Optional

import pandas as pd

from utils.logger import get_logger

log = get_logger("bars")

# Contagem-alvo de barras. Igual a contagem de candles de 4h sobre a mesma
# janela (2.000 = 333 dias), para que a comparacao meca ONDE as barras caem e
# nao QUANTAS existem -- a restricao estrutural desta hipotese.
BARRAS_ALVO_PADRAO = 2000

# Erro relativo aceito na calibracao. Medido convergindo em 2-3 iteracoes.
TOLERANCIA_PADRAO = 0.05
MAX_ITERACOES_PADRAO = 6

TIPOS = ("dollar", "cusum")


@dataclass
class ParametrosBarra:
    """Governa uma construcao. O limiar e DECLARADO, nunca varrido (FR-014)."""

    tipo: str = "dollar"
    limiar: Optional[float] = None
    barras_alvo: int = BARRAS_ALVO_PADRAO
    tolerancia: float = TOLERANCIA_PADRAO
    max_iteracoes: int = MAX_ITERACOES_PADRAO


def _validar(df: pd.DataFrame, tipo: str) -> None:
    if tipo not in TIPOS:
        raise ValueError(f"tipo de barra desconhecido: {tipo!r}; use um de {TIPOS}")
    if df is None or len(df) == 0:
        raise ValueError("serie vazia")
    faltando = {"open", "high", "low", "close"} - set(df.columns)
    if faltando:
        raise ValueError(f"colunas ausentes: {sorted(faltando)}")
    if tipo == "dollar":
        if "volume" not in df.columns:
            raise ValueError("barras por valor negociado exigem coluna 'volume'")
        if float(df["volume"].fillna(0).sum()) <= 0:
            # Volume zerado produziria uma unica barra com a serie inteira. Melhor
            # recusar que devolver uma barra silenciosamente errada.
            raise ValueError("volume totalmente nulo: impossivel construir barras")


def _fronteiras_dollar(df: pd.DataFrame, limiar: float) -> List[int]:
    """Indices de fechamento, um varrimento para a frente.

    A decisao de fechar em `i` usa apenas candles ate `i`. Nao existe caminho
    pelo qual um candle posterior influencie uma fronteira anterior.
    """
    fronteiras: List[int] = []
    acumulado = 0.0
    pares = zip(df["close"].values, df["volume"].values, strict=True)
    for i, (close, volume) in enumerate(pares):
        acumulado += float(close) * float(volume)
        if acumulado >= limiar:
            fronteiras.append(i)
            acumulado = 0.0
    return fronteiras


def _fronteiras_cusum(df: pd.DataFrame, limiar: float) -> List[int]:
    """Fecha quando o desvio acumulado, positivo ou negativo, cruza o limiar."""
    retornos = df["close"].pct_change().fillna(0.0).values
    fronteiras: List[int] = []
    s_pos = 0.0
    s_neg = 0.0
    for i, r in enumerate(retornos):
        s_pos = max(0.0, s_pos + float(r))
        s_neg = min(0.0, s_neg + float(r))
        if s_pos >= limiar or s_neg <= -limiar:
            fronteiras.append(i)
            s_pos = 0.0
            s_neg = 0.0
    return fronteiras


def _fronteiras(df: pd.DataFrame, tipo: str, limiar: float) -> List[int]:
    if limiar is None or not limiar > 0:
        raise ValueError(f"limiar precisa ser positivo, recebido {limiar!r}")
    return _fronteiras_dollar(df, limiar) if tipo == "dollar" else _fronteiras_cusum(df, limiar)


def construir_barras(
    df: pd.DataFrame,
    tipo: str = "dollar",
    limiar: Optional[float] = None,
    params: Optional[ParametrosBarra] = None,
) -> pd.DataFrame:
    """Agrupa candles inteiros em barras que fecham por atividade acumulada.

    A serie devolvida tem o MESMO contrato de colunas de uma serie de candles,
    para que indicadores, motor, walk-forward e validacao funcionem sem saber
    que a amostragem mudou (D5).

    A ultima barra e DESCARTADA quando nao cruzou o limiar: seu `close` seria o
    preco do instante em que os dados acabaram, e trata-lo como fechamento e
    transformar um instante arbitrario em decisao.
    """
    p = params or ParametrosBarra(tipo=tipo, limiar=limiar)
    tipo = p.tipo
    limiar = p.limiar if p.limiar is not None else limiar

    _validar(df, tipo)
    fronteiras = _fronteiras(df, tipo, limiar)
    if not fronteiras:
        return df.iloc[0:0].copy()

    linhas = []
    indices = []
    inicio = 0
    for fim in fronteiras:
        grupo = df.iloc[inicio:fim + 1]
        linhas.append({
            "open": float(grupo["open"].iloc[0]),
            "high": float(grupo["high"].max()),
            "low": float(grupo["low"].min()),
            "close": float(grupo["close"].iloc[-1]),
            "volume": float(grupo["volume"].sum()) if "volume" in grupo else 0.0,
            "candles_origem": len(grupo),
            "duracao_horas": _duracao_horas(grupo),
        })
        indices.append(grupo.index[-1])
        inicio = fim + 1

    return pd.DataFrame(linhas, index=pd.Index(indices, name=df.index.name))


def _duracao_horas(grupo: pd.DataFrame) -> float:
    try:
        delta = grupo.index[-1] - grupo.index[0]
        return float(delta.total_seconds()) / 3600.0
    except (AttributeError, TypeError):
        return 0.0


def calibrar_limiar(
    df: pd.DataFrame,
    tipo: str = "dollar",
    params: Optional[ParametrosBarra] = None,
) -> float:
    """Limiar que produz aproximadamente `barras_alvo` barras (D2).

    CONSULTA EXCLUSIVAMENTE A CONTAGEM DE BARRAS. Nenhuma metrica de retorno,
    drawdown ou profit factor participa. E calibracao de ESCALA, nao de
    desempenho -- a mesma defesa do alvo de volatilidade de H12, e pela mesma
    razao: o mecanismo precisa ser neutro em escala para que o que se meca seja
    o POSICIONAMENTO das barras, e nao a quantidade delas.

    Sem isto a comparacao seria entre 1.532 barras e 2.000 candles, o que mede
    tamanho de amostra, nao esquema de amostragem.

    Limiar ingenuo nao acerta o alvo porque a barra fecha AO CRUZAR e o candle
    que cruza costuma passar bastante do ponto. Medido: 1615/1366/1485 contra
    alvo de 2000. O passo `limiar <- limiar x contagem / alvo` converge em 2-3
    iteracoes.
    """
    p = params or ParametrosBarra(tipo=tipo)
    tipo = p.tipo
    _validar(df, tipo)

    limiar = _limiar_inicial(df, tipo, p.barras_alvo)
    for _ in range(p.max_iteracoes):
        contagem = len(_fronteiras(df, tipo, limiar))
        if contagem == 0:
            limiar /= 2.0
            continue
        erro = abs(contagem - p.barras_alvo) / p.barras_alvo
        if erro <= p.tolerancia:
            break
        limiar = limiar * contagem / p.barras_alvo
    return limiar


def _limiar_inicial(df: pd.DataFrame, tipo: str, alvo: int) -> float:
    if tipo == "dollar":
        total = float((df["close"] * df["volume"]).sum())
        return max(total / max(alvo, 1), 1e-12)
    # CUSUM: desvio tipico acumulado sobre o numero de candles que caberia numa
    # barra, se as barras fossem uniformes.
    passo = max(1, len(df) // max(alvo, 1))
    desvio = float(df["close"].pct_change().std() or 0.0)
    return max(desvio * (passo ** 0.5), 1e-12)


def diagnostico(barras: pd.DataFrame) -> dict:
    """Quanto a reamostragem de fato agrupou.

    E o numero que distingue "nao houve vantagem" de "o instrumento nao mediu
    nada". H12 teve 37 de 48 combinacoes inertes e so descobriu isso ao
    confrontar o fator medio observado com o previsto.
    """
    if barras is None or len(barras) == 0 or "candles_origem" not in barras:
        return {"barras": 0, "mediana": 0.0, "p90": 0.0, "pct_1_candle": 0.0}
    c = barras["candles_origem"]
    return {
        "barras": int(len(c)),
        "mediana": float(c.median()),
        "p90": float(c.quantile(0.9)),
        "pct_1_candle": float((c == 1).mean() * 100.0),
    }
