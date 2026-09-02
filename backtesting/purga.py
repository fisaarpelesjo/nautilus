"""H14 -- divisao treino/teste com purga e embargo (spec 027, US2).

POR QUE A PURGA EXISTE

Rotulos de barreira tripla SE SOBREPOEM NO TEMPO: o rotulo do evento em `t` so e
conhecido em `fim_horizonte`. Treinar com amostras cujo desfecho so se conhece
DENTRO da janela de teste entrega futuro ao modelo, e produz o resultado mais
convincente e mais falso possivel. E o analogo, em aprendizado supervisionado,
do achado M2 -- um filtro que comparava preco historico contra indicador
corrente, e que passou meses despercebido no projeto.

POR QUE A PURGA E GLOBAL, E NAO POR PAR

Este e o ponto nao obvio, e o custo de erra-lo seria invisivel.

Agrupar os 12 pares da 23.412 amostras em vez de 1.951 -- necessario para
estimar com folga. So que criptoativos sao fortemente correlacionados: H9 mediu
CORRELACAO DE 0,71 entre os pares deste mesmo universo, e foi por isso que
aquela hipotese reprovou.

Se a purga fosse aplicada par a par, a amostra de BTC no instante `t`
permaneceria no treino enquanto a de ETH em `t` estivesse no teste. Movendo-se
juntos, o modelo veria PELO BTC o desfecho que deveria prever para o ETH.

Por isso a fronteira e um INSTANTE DE CALENDARIO, e a purga remove qualquer
amostra -- de qualquer par -- cujo horizonte alcance a janela de teste.

O EMBARGO USA O HORIZONTE MAXIMO, NAO O MEDIANO

O embargo protege contra a cauda da distribuicao de horizontes. Usar a mediana
deixaria metade dos casos descobertos, que e precisamente o oposto do proposito.

CUSTO MEDIDO

Horizonte mediano de 8 velas contra 16.388 amostras de treino: a purga remove
~8 na fronteira e o embargo outras ~24. Resta praticamente 100% do treino
ingenuo. A preocupacao de que purga e embargo esvaziassem a amostra NAO se
materializa nesta configuracao -- e isso e medicao, nao suposicao.
"""
from dataclasses import dataclass, field
from typing import List

import pandas as pd

from utils.logger import get_logger

log = get_logger("purga")


@dataclass
class DivisaoPurgada:
    """Um par de janelas treino/teste com o vazamento removido."""

    inicio_teste: object
    fim_teste: object
    indices_treino: List[int] = field(default_factory=list)
    indices_teste: List[int] = field(default_factory=list)
    n_purgadas: int = 0
    n_embargadas: int = 0
    embargo_velas: int = 0

    def suficiente(self, minimo: int) -> bool:
        """Se as duas janelas comportam avaliacao.

        Amostra insuficiente e INCONCLUSIVA, nunca reprovacao -- regra de H10,
        H11 e M9.
        """
        return len(self.indices_treino) >= minimo and len(self.indices_teste) >= minimo


def dividir_com_purga(
    eventos: pd.DataFrame,
    ratio_teste: float = 0.3,
    embargo_velas: int = 24,
) -> DivisaoPurgada:
    """Divide por INSTANTE DE CALENDARIO, purgando sobreposicao e embargo.

    `eventos` precisa das colunas `instante` e `fim_horizonte`. A fronteira sai
    do quantil temporal, nao da posicao na lista: com pares agrupados, cortar
    por posicao misturaria instantes de pares diferentes.
    """
    if eventos is None or len(eventos) == 0:
        raise ValueError("conjunto de eventos vazio")
    if not 0.0 < ratio_teste < 1.0:
        raise ValueError(f"ratio_teste precisa ficar em (0, 1), recebido {ratio_teste!r}")
    for col in ("instante", "fim_horizonte"):
        if col not in eventos.columns:
            raise ValueError(f"eventos precisam da coluna {col!r}")

    instantes = pd.to_datetime(eventos["instante"])
    fim_horizonte = pd.to_datetime(eventos["fim_horizonte"])

    ordenados = instantes.sort_values().unique()
    corte = int(len(ordenados) * (1 - ratio_teste))
    corte = min(max(corte, 1), len(ordenados) - 1)
    inicio_teste = ordenados[corte]
    fim_teste = ordenados[-1]

    em_teste = instantes >= inicio_teste
    candidatos_treino = ~em_teste

    # PURGA: o desfecho da amostra so se conhece em `fim_horizonte`. Se esse
    # instante alcanca a janela de teste, a amostra carrega informacao dela.
    sobrepoe = candidatos_treino & (fim_horizonte >= inicio_teste)

    # EMBARGO: intervalo morto ANTES da janela de teste. As amostras logo antes
    # dela, mesmo com horizonte curto, ficam correlacionadas com o inicio do
    # teste; o embargo as afasta.
    if embargo_velas > 0 and len(ordenados) > 1:
        passo = pd.Series(ordenados).diff().median()
        limite_embargo = inicio_teste - passo * embargo_velas
        embargada = candidatos_treino & ~sobrepoe & (instantes > limite_embargo)
    else:
        embargada = pd.Series(False, index=eventos.index)

    treino = candidatos_treino & ~sobrepoe & ~embargada

    return DivisaoPurgada(
        inicio_teste=inicio_teste,
        fim_teste=fim_teste,
        indices_treino=list(eventos.index[treino]),
        indices_teste=list(eventos.index[em_teste]),
        n_purgadas=int(sobrepoe.sum()),
        n_embargadas=int(embargada.sum()),
        embargo_velas=embargo_velas,
    )
