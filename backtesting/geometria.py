"""H20 -- perfis de geometria de barreira e regra de selecao (spec 028).

O QUE ESTE MODULO E, E O QUE ELE NAO PODE SER

H20 e estruturalmente uma varredura de parametro -- a coisa que a metodologia
deste projeto mais combate. A diferenca entre pesquisa legitima e testes
multiplos disfarcados esta inteiramente em tres restricoes, e este modulo existe
para torna-las verificaveis:

  FR-003  a regra de selecao foi escrita ANTES da medicao (commit 7cc19e0) e
          aparece no relatorio
  FR-004  a regra NAO consulta desempenho de modelo algum
  FR-014  exatamente UMA geometria e avaliada com modelo

A medicao de perfis (`medir_perfis`) roda sobre todas as candidatas porque nao
treina nada -- e rotulagem pura. A selecao (`selecionar`) escolhe uma, por regra
fixa. Quem avalia com modelo e `backtesting/modelo.py`, uma vez.

A TESE DE H20 FOI REFUTADA POR ESTE MODULO

Medido: a razao de chances cai MAIS RAPIDO que o ponto de empate conforme o alvo
se afasta. A folga vai de +0,3% em tp=2,0 a -48% em tp=6,0. A hipotese propunha
que afastar o alvo baixaria o obstaculo; os dados fazem o contrario, e de forma
monotona.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from strategy.barreira_tripla import (
    ParametrosBarreira,
    distribuicao_classes,
    rotular,
)
from utils.logger import get_logger

log = get_logger("geometria")

# Conjunto candidato DECLARADO (D1). Stop fixo: variar os dois eixos
# multiplicaria o conjunto sem responder nada que o eixo do alvo nao responda, e
# o stop tem significado operacional proprio -- limita a perda por operacao.
SL_FIXO = 1.5
TPS_CANDIDATOS = (2.0, 2.5, 3.0, 4.0, 5.0, 6.0)
TP_REFERENCIA = 3.0
LIMITE_VELAS = 24

# Elevacao relativa MEDIDA em H14 (0,3896 -> 0,5134; z = +5,21, p < 0,0001).
# Usada para FORMULAR a regra, nunca como resultado da geometria nova (FR-008).
ELEVACAO_H14 = 1.318

# Folga exigida sobre o empate. NAO e escolha: sai do poder estatistico de H14.
# Com 1.580 decisoes, rejeitar o empate a 5% unilateral exige fracao de alvos
# acima de 0,3333 + 1,645 x 18,7/1580 = 0,3528, isto e razao acima de 0,545
# contra empate 0,500 -- folga de +9%. Exigir menos selecionaria geometria em
# que, mesmo dando tudo certo, o resultado ficaria dentro do ruido. Foi
# exatamente o que aconteceu em H14, e e o achado M13.
FOLGA = 1.09

# Em tp=3,0 a medicao deu 12,8% terminando por limite de tempo. A razao de
# chances descreve so os eventos que tocam alvo ou stop (FR-009); acima de um
# quarto da amostra terminando por tempo, ela fala de uma minoria e a comparacao
# entre geometrias perde sentido.
TETO_PCT_TEMPO = 25.0

# H14 operou com 1.580 desfechos e nao resolveu a margem. Abaixo de 1.000 o
# resultado seria inconclusivo por construcao.
MIN_DESFECHOS = 1000


@dataclass
class PerfilGeometria:
    """Medicao de uma geometria, SEM modelo algum."""

    tp_mult: float
    sl_mult: float = SL_FIXO
    limite_velas: int = LIMITE_VELAS
    n_alvo: int = 0
    n_stop: int = 0
    n_tempo: int = 0
    erro: str = ""

    @property
    def n_total(self) -> int:
        return self.n_alvo + self.n_stop + self.n_tempo

    @property
    def n_desfechos(self) -> int:
        """Eventos que tocaram alvo ou stop. O limite de tempo nao e desfecho."""
        return self.n_alvo + self.n_stop

    @property
    def pct_tempo(self) -> float:
        return self.n_tempo / self.n_total * 100 if self.n_total else 0.0

    @property
    def razao_base(self) -> Optional[float]:
        if self.n_stop == 0:
            return float("inf") if self.n_alvo > 0 else None
        return self.n_alvo / self.n_stop

    @property
    def empate(self) -> float:
        return self.sl_mult / self.tp_mult

    @property
    def elegivel(self) -> bool:
        return not self.motivos_inelegibilidade

    @property
    def motivos_inelegibilidade(self) -> List[str]:
        """Quais criterios falharam. Lista vazia significa elegivel."""
        if self.erro:
            return [f"erro: {self.erro}"]
        r = self.razao_base
        falhas = []
        if r is None or r * ELEVACAO_H14 < self.empate * FOLGA:
            falhas.append("c1 margem")
        if self.pct_tempo > TETO_PCT_TEMPO:
            falhas.append("c2 limite de tempo")
        if self.n_desfechos < MIN_DESFECHOS:
            falhas.append("c3 amostra")
        return falhas


@dataclass
class RelatorioGeometria:
    perfis: List[PerfilGeometria] = field(default_factory=list)
    selecionada: Optional[PerfilGeometria] = None
    regra: str = ""


def regra_declarada() -> str:
    """Texto da regra, exibido no relatorio (FR-003).

    Existe como funcao para que o relatorio nao possa divergir do codigo: o que
    e exibido e o que e aplicado.
    """
    return (
        f"elegivel quando (1) razao_base x {ELEVACAO_H14} >= empate x {FOLGA}, "
        f"(2) pct por limite de tempo <= {TETO_PCT_TEMPO:.0f}%, "
        f"(3) desfechos alvo|stop >= {MIN_DESFECHOS}; "
        f"entre as elegiveis, seleciona a de MENOR tp"
    )


def medir_perfis(
    preparados: Dict,
    tps=TPS_CANDIDATOS,
    sl_mult: float = SL_FIXO,
    limite_velas: int = LIMITE_VELAS,
) -> List[PerfilGeometria]:
    """Rotula cada geometria candidata e conta desfechos. NAO treina modelo.

    `preparados` mapeia par -> DataFrame ja com indicadores. Roda sobre todas as
    candidatas porque nada aqui e avaliacao: e propriedade da serie.
    """
    perfis = []
    for tp in tps:
        p = ParametrosBarreira(sl_mult=sl_mult, tp_mult=tp, limite_velas=limite_velas)
        perfil = PerfilGeometria(tp_mult=tp, sl_mult=sl_mult, limite_velas=limite_velas)
        for par, prep in preparados.items():
            try:
                bruto = rotular(prep, p)["rotulo_bruto"].dropna()
            except Exception as exc:
                log.warning(f"{par} tp={tp}: {type(exc).__name__}: {str(exc)[:60]}")
                continue
            d = distribuicao_classes(bruto)
            n = d["n"]
            perfil.n_alvo += round(d["alvo"] / 100 * n)
            perfil.n_stop += round(d["stop"] / 100 * n)
            perfil.n_tempo += round(d["tempo"] / 100 * n)
        if perfil.n_total == 0:
            perfil.erro = "nenhum evento rotulavel"
        perfis.append(perfil)
    return perfis


def selecionar(perfis: List[PerfilGeometria]) -> Optional[PerfilGeometria]:
    """Aplica a regra declarada. Deterministica (FR-005).

    Seleciona a de MENOR `tp` entre as elegiveis -- nao a de maior margem.
    Maximizar a margem seria otimizar sobre o conjunto e reintroduziria o
    problema de testes multiplos por outra porta.

    Nenhuma elegivel devolve `None`, e isso e desfecho legitimo (FR-006): H20
    encerraria sem avaliacao de modelo. A regra NAO e relaxada.
    """
    elegiveis = [p for p in perfis if p.elegivel]
    return min(elegiveis, key=lambda p: p.tp_mult) if elegiveis else None


def run_geometria_scan(pares=None, tps=TPS_CANDIDATOS) -> RelatorioGeometria:
    """Mede os perfis e aplica a regra. Nenhum modelo e treinado aqui."""
    from backtesting.horizonte import UNIVERSO_H11, preparar
    from config.settings import TIMEFRAME
    from data.fetcher import fetch_ohlcv
    from strategy.ema_rsi import EmaRsiStrategy

    pares = pares if pares is not None else UNIVERSO_H11
    estrategia = EmaRsiStrategy()

    preparados = {}
    for par in pares:
        try:
            prep = preparar(fetch_ohlcv(par, TIMEFRAME, 2000), estrategia)
        except Exception as exc:
            log.warning(f"{par}: {type(exc).__name__}: {str(exc)[:60]}")
            continue
        if prep is not None:
            preparados[par] = prep

    perfis = medir_perfis(preparados, tps=tps)
    return RelatorioGeometria(
        perfis=perfis, selecionada=selecionar(perfis), regra=regra_declarada(),
    )


__all__ = [
    "ELEVACAO_H14",
    "FOLGA",
    "MIN_DESFECHOS",
    "SL_FIXO",
    "TETO_PCT_TEMPO",
    "TPS_CANDIDATOS",
    "TP_REFERENCIA",
    "PerfilGeometria",
    "RelatorioGeometria",
    "medir_perfis",
    "regra_declarada",
    "run_geometria_scan",
    "selecionar",
]
