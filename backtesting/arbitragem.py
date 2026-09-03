"""H15 -- arbitragem entre corretoras (spec 029).

Instrumento de amostragem, nao veredito: mede o diferencial liquido de
arbitragem entre pares de corretoras via livro de ofertas publico, qualifica
por latencia e persiste para acumular amostra entre execucoes. Ver
specs/029-arbitragem-entre-corretoras/{spec,plan,data-model,research}.md.

Nao envia ordem alguma (FR-012) e nao exige chave de API (FR-013) -- so
consulta fetch_order_book publico, nas seis corretoras declaradas em D1.
"""

import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from itertools import combinations
from typing import Optional

import ccxt

from data.arbitragem_store import registrar_observacoes
from utils.logger import get_logger

log = get_logger("arbitragem")

# D1 -- selecionadas por acessibilidade publica e liquidez, nunca por
# diferencial observado (research.md). Kraken entra apesar de cara/lenta:
# exclui-la seria selecionar pelo resultado esperado.
CORRETORAS = ("binance", "bybit", "okx", "kucoin", "gate", "kraken")

# D3 -- taxa publica de tomador de liquidez, sem desconto por volume.
# Arbitragem exige execucao imediata; taxa de provedor assumiria que a ordem
# repousa no livro, contradizendo a tese.
TAXA_TOMADOR = {
    "binance": 0.00100,
    "bybit": 0.00100,
    "kucoin": 0.00100,
    "okx": 0.00150,
    "gate": 0.00200,
    "kraken": 0.00400,
}

# D2 -- a esse volume o slippage medido e 0,0000% em 5 das 6 corretoras
# (kraken 0,0018%): profundidade nao e o gargalo, o topo do livro descreve
# bem o preco de execucao.
VOLUME_USDT_PADRAO = 10_000.0

# D4 -- duas leituras a ~342ms medianos somam ~700ms; o teto da quase 3x de
# folga. Acima disso as duas pontas descrevem instantes distantes demais.
TETO_LATENCIA_MS = 2000

# Fase 1 (data-model.md) -- regra pratica de estabilidade de media, nao
# derivada dos dados. Mesmo espirito de MIN_DESFECHOS em backtesting/geometria.py.
MIN_OBSERVACOES_AGREGACAO = 30


def normalizar_niveis(raw: list) -> list[tuple[float, float]]:
    """Normaliza niveis de livro para (preco, quantidade).

    Kraken e OKX devolvem tres campos por nivel (preco, qtd, instante do
    nivel); as demais corretoras devolvem dois (D1, achado de implementacao).
    O terceiro campo, quando presente, e descartado -- o instante que importa
    para o teto de latencia (D4) e o da LeituraLivro inteira, nao por nivel.
    """
    niveis = []
    for nivel in raw or []:
        preco, qtd = nivel[0], nivel[1]
        niveis.append((float(preco), float(qtd)))
    return niveis


@dataclass
class LeituraLivro:
    corretora: str
    par: str
    instante: float
    bids: list[tuple[float, float]] = field(default_factory=list)
    asks: list[tuple[float, float]] = field(default_factory=list)
    erro: Optional[str] = None

    @property
    def sucesso(self) -> bool:
        return self.erro is None


_exchange_cache: dict[str, "ccxt.Exchange"] = {}
_exchange_cache_lock = threading.Lock()


def _get_exchange_publico(corretora: str) -> "ccxt.Exchange":
    """Instancia ccxt publica (sem apiKey/secret) por corretora, cacheada.

    Nunca autenticada -- FR-013 nao exige chave de API para nenhuma das seis
    corretoras. Mesmo espirito de data/fetcher.py::get_exchange, mas por id
    de corretora em vez de um unico exchange fixo.

    Lock defensivo (spec 053): `medir_ciclo` chama isto de threads
    diferentes em paralelo. Na pratica cada thread usa uma chave (corretora)
    distinta, entao nunca disputam a mesma entrada -- mas escrever no dict
    sem lock dependeria implicitamente de garantias do GIL do CPython, nao
    de uma garantia da API do dict.
    """
    if corretora in _exchange_cache:
        return _exchange_cache[corretora]
    with _exchange_cache_lock:
        if corretora not in _exchange_cache:
            classe = getattr(ccxt, corretora)
            _exchange_cache[corretora] = classe({"enableRateLimit": True, "timeout": 10000})
    return _exchange_cache[corretora]


def reset_exchange_cache() -> None:
    """Limpa o cache de instancias -- uso em testes."""
    _exchange_cache.clear()


def ler_livro(corretora: str, par: str) -> LeituraLivro:
    """Le o livro de ofertas publico de `par` em `corretora`.

    Falha de rede/simbolo inexistente nunca levanta excecao para o chamador
    -- vira LeituraLivro(erro=...), para que medir_ciclo continue com as
    demais corretoras (FR-011).
    """
    try:
        exchange = _get_exchange_publico(corretora)
        book = exchange.fetch_order_book(par)
    except Exception as exc:
        log.warning(f"Falha ao ler livro de {par} em {corretora}: {exc}")
        return LeituraLivro(corretora=corretora, par=par, instante=time.monotonic(), erro=str(exc))

    return LeituraLivro(
        corretora=corretora,
        par=par,
        instante=time.monotonic(),
        bids=normalizar_niveis(book.get("bids")),
        asks=normalizar_niveis(book.get("asks")),
    )


def preco_medio_execucao(niveis: list[tuple[float, float]], volume_usdt: float) -> tuple[float, float]:
    """Preco medio de execucao para `volume_usdt`, caminhando os niveis a
    partir do melhor preco -- nunca so o topo do livro (FR-001).

    Retorna (preco_medio, volume_preenchido_usdt). Quando o livro nao
    comporta o volume inteiro, `volume_preenchido_usdt < volume_usdt` e o
    preco medio reflete so o que foi possivel preencher (FR-007) -- nunca
    extrapola alem da profundidade real.
    """
    restante = volume_usdt
    custo_total = 0.0
    qtd_total = 0.0
    for preco, qtd in niveis:
        if preco <= 0 or qtd <= 0:
            continue
        valor_nivel = preco * qtd
        consumido = min(restante, valor_nivel)
        custo_total += consumido
        qtd_total += consumido / preco
        restante -= consumido
        if restante <= 0:
            break

    if qtd_total <= 0:
        return 0.0, 0.0

    preco_medio = custo_total / qtd_total
    volume_preenchido = volume_usdt - restante
    return preco_medio, volume_preenchido


@dataclass
class Comparacao:
    corretora_compra: str
    corretora_venda: str
    preco_medio_compra: float
    preco_medio_venda: float
    volume_preenchido_usdt: float
    diferencial_bruto_pct: float
    custo_pct: Optional[float]
    diferencial_liquido_pct: Optional[float]
    estado: str
    intervalo_ms: float = 0.0
    instante_registro: float = field(default_factory=time.time)


def _direcao(compra: LeituraLivro, venda: LeituraLivro, volume_usdt: float) -> dict:
    preco_medio_compra, vol_compra = preco_medio_execucao(compra.asks, volume_usdt)
    preco_medio_venda, vol_venda = preco_medio_execucao(venda.bids, volume_usdt)
    if preco_medio_compra > 0:
        diferencial_bruto_pct = (preco_medio_venda - preco_medio_compra) / preco_medio_compra
    else:
        diferencial_bruto_pct = 0.0
    return {
        "preco_medio_compra": preco_medio_compra,
        "preco_medio_venda": preco_medio_venda,
        "volume_preenchido_usdt": min(vol_compra, vol_venda),
        "diferencial_bruto_pct": diferencial_bruto_pct,
    }


def comparar(leitura_a: LeituraLivro, leitura_b: LeituraLivro, volume_usdt: float = VOLUME_USDT_PADRAO) -> Comparacao:
    """Compara duas leituras de livro, escolhendo a direcao (compra/venda)
    com maior diferencial bruto entre as duas possiveis, e classifica o
    resultado (data-model.md -- a ordem das checagens e a regra):

    1. `custo_desconhecido` -- taxa de alguma corretora fora de TAXA_TOMADOR
       (FR-006, precede tudo: custo desconhecido nunca vira zero)
    2. `profundidade_insuficiente` -- preco medio sobre volume parcial (FR-007)
    3. `latencia_alta` -- intervalo entre as duas leituras acima do teto
       (FR-005): um diferencial calculado entre leituras separadas por mais
       de TETO_LATENCIA_MS nao descreve um instante que existiu em lugar
       nenhum, mesmo que o liquido desse positivo
    4. `oportunidade` / `sem_oportunidade` -- classificacao final, so quando
       as tres checagens anteriores passam
    """
    dir_ab = _direcao(leitura_a, leitura_b, volume_usdt)
    dir_ba = _direcao(leitura_b, leitura_a, volume_usdt)

    if dir_ab["diferencial_bruto_pct"] >= dir_ba["diferencial_bruto_pct"]:
        corretora_compra, corretora_venda, d = leitura_a.corretora, leitura_b.corretora, dir_ab
        leitura_compra, leitura_venda = leitura_a, leitura_b
    else:
        corretora_compra, corretora_venda, d = leitura_b.corretora, leitura_a.corretora, dir_ba
        leitura_compra, leitura_venda = leitura_b, leitura_a

    intervalo_ms = abs(leitura_venda.instante - leitura_compra.instante) * 1000

    taxa_compra = TAXA_TOMADOR.get(corretora_compra)
    taxa_venda = TAXA_TOMADOR.get(corretora_venda)

    if taxa_compra is None or taxa_venda is None:
        custo_pct = None
        diferencial_liquido_pct = None
        estado = "custo_desconhecido"
    else:
        custo_pct = taxa_compra + taxa_venda
        diferencial_liquido_pct = d["diferencial_bruto_pct"] - custo_pct
        if d["volume_preenchido_usdt"] < volume_usdt:
            estado = "profundidade_insuficiente"
        elif intervalo_ms > TETO_LATENCIA_MS:
            estado = "latencia_alta"
        elif diferencial_liquido_pct > 0:
            estado = "oportunidade"
        else:
            estado = "sem_oportunidade"

    return Comparacao(
        corretora_compra=corretora_compra,
        corretora_venda=corretora_venda,
        preco_medio_compra=d["preco_medio_compra"],
        preco_medio_venda=d["preco_medio_venda"],
        volume_preenchido_usdt=d["volume_preenchido_usdt"],
        diferencial_bruto_pct=d["diferencial_bruto_pct"],
        custo_pct=custo_pct,
        diferencial_liquido_pct=diferencial_liquido_pct,
        estado=estado,
        intervalo_ms=intervalo_ms,
    )


def mesma_cotacao(leitura_a: LeituraLivro, leitura_b: LeituraLivro) -> tuple[bool, Optional[str]]:
    """Compara so entre pares de mesma moeda de cotacao (FR-003).

    Comparar `BTC/USDT` com `BTC/USD` mistura o diferencial de arbitragem
    com o desvio de paridade USDT/USD -- medido em research.md: 0,104% entre
    cotacoes diferentes contra 0,037% entre iguais, a maior parte do
    "diferencial" era so a paridade.
    """
    cotacao_a = leitura_a.par.split("/")[1]
    cotacao_b = leitura_b.par.split("/")[1]
    if cotacao_a != cotacao_b:
        motivo = (f"cotacoes diferentes: {cotacao_a} ({leitura_a.corretora}) "
                  f"vs {cotacao_b} ({leitura_b.corretora})")
        return False, motivo
    return True, None


def medir_ciclo(
    par: str, volume_usdt: float = VOLUME_USDT_PADRAO,
) -> tuple[list[Comparacao], list[str], list[tuple[str, str, str]]]:
    """Um ciclo de medicao: le o livro de `par` nas seis corretoras (D1) e
    compara cada combinacao entre as que responderam e tem a mesma cotacao.

    Falha isolada de uma corretora nunca aborta o ciclo (FR-011) -- ela so
    fica de fora das combinacoes e aparece na lista de indisponiveis. Par de
    cotacao diferente nunca vira Comparacao (FR-003) -- aparece em
    `pares_recusados` com o motivo, nunca silenciosamente incluido.

    Leitura em PARALELO (spec 053, M15): ler_livro e I/O de rede sincrono
    que libera o GIL durante a espera -- threads bastam. Sequencial fazia o
    intervalo entre a primeira e a ultima corretora ultrapassar sozinho o
    teto de latencia (TETO_LATENCIA_MS) antes mesmo de qualquer comparacao
    ser calculada -- medido: so 1 das 15 combinacoes possiveis (as
    adjacentes na ordem fixa de leitura) alguma vez ficava abaixo do teto.
    """
    with ThreadPoolExecutor(max_workers=len(CORRETORAS)) as executor:
        resultados = list(executor.map(lambda c: ler_livro(c, par), CORRETORAS))
    leituras = dict(zip(CORRETORAS, resultados, strict=True))
    indisponiveis = [corretora for corretora, leitura in leituras.items() if not leitura.sucesso]
    disponiveis = [leitura for leitura in leituras.values() if leitura.sucesso]

    comparacoes = []
    pares_recusados: list[tuple[str, str, str]] = []
    for leitura_a, leitura_b in combinations(disponiveis, 2):
        compativel, motivo = mesma_cotacao(leitura_a, leitura_b)
        if not compativel:
            pares_recusados.append((leitura_a.corretora, leitura_b.corretora, motivo))
            continue
        comparacoes.append(comparar(leitura_a, leitura_b, volume_usdt))

    registrar_observacoes(comparacoes)
    return comparacoes, indisponiveis, pares_recusados


_MOTIVO_INEXECUTAVEL = (
    "capital pre-posicionado nas duas corretoras, chaves de API em multiplas "
    "corretoras e execucao simultanea das duas pernas -- nenhum dos tres esta "
    "implementado (D6)"
)


@dataclass
class RelatorioH15:
    comparacoes_ciclo: list[Comparacao]
    corretoras_indisponiveis: list[str]
    pares_recusados: list[tuple[str, str, str]]
    periodo_coberto: Optional[tuple[float, float]]
    n_observacoes_total: int
    n_observacoes_por_combinacao: dict[tuple[str, str], int]
    estado_agregado: str
    executavel_em_producao: bool = False
    motivo_executabilidade: str = _MOTIVO_INEXECUTAVEL


def agregar(
    comparacoes_ciclo: list[Comparacao],
    corretoras_indisponiveis: list[str],
    pares_recusados: list[tuple[str, str, str]],
    observacoes_historico: list[dict],
) -> RelatorioH15:
    """Agrega **todo** o historico persistido (FR-009), nao so o ciclo atual.

    `estado_agregado` e so descritivo ("inconclusivo"/"amostra_suficiente")
    -- nunca aprovado/reprovado. O veredito de H15 exige tempo decorrido
    (spec.md, Assumptions); calcular um aqui repetiria o erro que a
    Iteracao 1 do checklist ja corrigiu (spec original prometia veredito).
    """
    if observacoes_historico:
        instantes = [o["instante_registro"] for o in observacoes_historico if "instante_registro" in o]
        periodo_coberto = (min(instantes), max(instantes)) if instantes else None
    else:
        periodo_coberto = None

    # Agrupado por par NAO ORDENADO de corretoras -- comparar() escolhe a
    # direcao (quem compra/quem vende) mais favoravel a cada ciclo, entao a
    # mesma combinacao de corretoras pode trocar de direcao entre execucoes.
    # Contar por direcao fragmentaria a mesma combinacao em duas contagens.
    n_por_combinacao: dict[tuple[str, str], int] = {}
    for o in observacoes_historico:
        chave = tuple(sorted((o.get("corretora_compra", ""), o.get("corretora_venda", ""))))
        n_por_combinacao[chave] = n_por_combinacao.get(chave, 0) + 1

    maior_combinacao = max(n_por_combinacao.values(), default=0)
    estado_agregado = (
        "amostra_suficiente" if maior_combinacao >= MIN_OBSERVACOES_AGREGACAO else "inconclusivo"
    )

    return RelatorioH15(
        comparacoes_ciclo=comparacoes_ciclo,
        corretoras_indisponiveis=corretoras_indisponiveis,
        pares_recusados=pares_recusados,
        periodo_coberto=periodo_coberto,
        n_observacoes_total=len(observacoes_historico),
        n_observacoes_por_combinacao=n_por_combinacao,
        estado_agregado=estado_agregado,
    )
