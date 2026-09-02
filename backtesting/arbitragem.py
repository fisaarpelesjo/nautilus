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
