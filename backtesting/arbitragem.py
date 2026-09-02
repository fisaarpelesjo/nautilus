"""H15 -- arbitragem entre corretoras (spec 029).

Instrumento de amostragem, nao veredito: mede o diferencial liquido de
arbitragem entre pares de corretoras via livro de ofertas publico, qualifica
por latencia e persiste para acumular amostra entre execucoes. Ver
specs/029-arbitragem-entre-corretoras/{spec,plan,data-model,research}.md.

Nao envia ordem alguma (FR-012) e nao exige chave de API (FR-013) -- so
consulta fetch_order_book publico, nas seis corretoras declaradas em D1.
"""

import time
from dataclasses import dataclass, field
from itertools import combinations
from typing import Optional

import ccxt

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


def _get_exchange_publico(corretora: str) -> "ccxt.Exchange":
    """Instancia ccxt publica (sem apiKey/secret) por corretora, cacheada.

    Nunca autenticada -- FR-013 nao exige chave de API para nenhuma das seis
    corretoras. Mesmo espirito de data/fetcher.py::get_exchange, mas por id
    de corretora em vez de um unico exchange fixo.
    """
    if corretora in _exchange_cache:
        return _exchange_cache[corretora]
    classe = getattr(ccxt, corretora)
    exchange = classe({"enableRateLimit": True, "timeout": 10000})
    _exchange_cache[corretora] = exchange
    return exchange


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
    3. `oportunidade` / `sem_oportunidade` -- classificacao final

    `latencia_alta` (US3) ainda nao existe aqui -- entra depois, entre 2 e 3.
    """
    dir_ab = _direcao(leitura_a, leitura_b, volume_usdt)
    dir_ba = _direcao(leitura_b, leitura_a, volume_usdt)

    if dir_ab["diferencial_bruto_pct"] >= dir_ba["diferencial_bruto_pct"]:
        corretora_compra, corretora_venda, d = leitura_a.corretora, leitura_b.corretora, dir_ab
    else:
        corretora_compra, corretora_venda, d = leitura_b.corretora, leitura_a.corretora, dir_ba

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
    """
    leituras = {corretora: ler_livro(corretora, par) for corretora in CORRETORAS}
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

    return comparacoes, indisponiveis, pares_recusados
