"""H12 — Dimensionamento de posicao por volatilidade (volatility targeting).

TESE

Alocar valor nocional constante em ativos de volatilidade variavel significa
assumir risco variavel. Escalar a posicao inversamente a volatilidade realizada
mantem a EXPOSICAO AO RISCO aproximadamente constante -- e o mecanismo padrao de
controle de drawdown em gestao sistematica.

MOTIVACAO VEM DE DENTRO DO REGISTRO

H7 (momentum transversal) reprovou com drawdown de 11,76% contra o teto de
10,0%. Profit factor, numero de operacoes e retorno contra buy-and-hold todos
passavam. Foi a UNICA hipotese da investigacao a falhar exclusivamente no limite
de risco. Se o excesso de drawdown for consequencia do dimensionamento, H12
traz H7 de volta para dentro do teto e ela volta a ser testavel.

O TETO DO FATOR E INVARIANTE DE CODIGO

    fator = min(1.0, alvo / atr_ratio)

O `min` nao e validacao defensiva, e a fórmula. FR-003 proibe ampliar a posicao,
e a constituicao do projeto proibe alavancagem (`max_leverage = 1`). Com o teto
aqui, nao existe caminho pelo qual esta feature aumente exposicao -- nem por
alvo mal configurado, nem por volatilidade anormalmente baixa.

POR QUE risk/manager.py NAO E TOCADO

E caminho de producao, sujeito ao principio Safety First. FR-013 exige que o bot
em execucao nao mude enquanto nenhuma hipotese for aprovada. O dimensionamento
vive atras de um parametro opcional de `simulate_backtest` cujo default
reproduz o comportamento atual byte a byte.

O QUE ESTE MODULO MEDE

Nao "a versao dimensionada e boa?", mas "ela e melhor que a MESMA estrategia sem
dimensionamento?". Dai a unidade de analise ser a comparacao pareada, e nao a
combinacao isolada.

E o risco dominante da avaliacao esta declarado na spec: dimensionar por
volatilidade reduz exposicao por construcao -- fator medio 0,90 na medicao de
`research.md`, ou seja ~10% menos exposicao. Num mercado em queda isso sozinho
melhora o retorno relativo ao buy-and-hold sem qualquer capacidade de selecao.
E o achado M7. Por isso `sem_vantagem` existe como estado proprio.
"""
import math
from dataclasses import dataclass, field
from typing import List, Optional

from utils.logger import get_logger

log = get_logger("volatilidade")

# Alvo derivado da mediana observada de `atr_ratio` (0,0187 em 23.412
# observacoes de 4h, 12 pares, 2026-09-01). Escolhido para o mecanismo ser
# NEUTRO NA ESCALA MEDIA, nao para maximizar desempenho: nenhum alvo foi
# testado contra retorno antes de ser fixado. Ver research.md D3.
ALVO_PADRAO = 0.02

# Piso do fator. Evita que volatilidade extrema produza posicao tao pequena que
# a ordem sequer seja aceita pela corretora -- caso de borda da spec.
FATOR_MINIMO_PADRAO = 0.20


@dataclass
class ParametrosVolatilidade:
    alvo: float = ALVO_PADRAO
    fator_minimo: float = FATOR_MINIMO_PADRAO


def fator_volatilidade(atr_ratio, params: Optional[ParametrosVolatilidade] = None) -> float:
    """Multiplicador do tamanho da posicao, em (fator_minimo, 1.0].

        fator = min(1.0, alvo / atr_ratio)

    O `min` e a formula, nao validacao: FR-003 e a proibicao de alavancagem da
    constituicao dependem de nao existir caminho que devolva mais que 1,0.

    `atr_ratio` invalido -- ausente, nulo, negativo ou nao finito -- devolve
    1,0, isto e, o tamanho que o sistema ja calcularia. Recair no vigente e a
    politica de falha do projeto: dado desconhecido nunca vira decisao
    silenciosa, e as alternativas seriam divisao por zero ou posicao infinita.
    """
    p = params or ParametrosVolatilidade()

    try:
        v = float(atr_ratio)
    except (TypeError, ValueError):
        return 1.0

    if not math.isfinite(v) or v <= 0:
        return 1.0

    return max(p.fator_minimo, min(1.0, p.alvo / v))


@dataclass
class ComparacaoPareada:
    estrategia: str
    par: str
    sem_dimensionamento: object = None
    com_dimensionamento: object = None
    folds_base: List = field(default_factory=list)
    folds_dim: List = field(default_factory=list)
    retorno_sem_custo_base: Optional[float] = None
    retorno_sem_custo_dim: Optional[float] = None
    fator_medio: float = 1.0
    status: str = "inconclusivo"
    motivo: str = ""


def comparar_combinacao(*args, **kwargs) -> ComparacaoPareada:
    raise NotImplementedError("T015")


def run_volatilidade_scan(*args, **kwargs) -> List[ComparacaoPareada]:
    raise NotImplementedError("T016")
