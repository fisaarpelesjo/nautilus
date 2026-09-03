"""H22 -- arbitragem triangular intra-corretora (spec 060).

Instrumento de amostragem, nao veredito -- mesmo principio de H15
(`backtesting/arbitragem.py`, spec 029): mede o diferencial liquido de um
ciclo de tres pernas DENTRO DA MESMA CORRETORA via livro de ofertas
publico, qualifica por profundidade/latencia e persiste para acumular
amostra entre execucoes. Ver
specs/060-h22-arbitragem-triangular/{spec,research}.md.

Diferente de H15 (duas pernas, corretoras diferentes, obstaculo dominante
e latencia de rede entre corretoras + capital pre-posicionado em cada
uma), aqui as tres pernas estao na MESMA corretora -- o obstaculo
estrutural de H15 nao se aplica; a preocupacao aqui e concorrencia com
bots de alta frequencia que operam na escala de milissegundos.

Nao envia ordem alguma e nao exige chave de API -- so consulta
fetch_order_book publico via a instancia spot ja cacheada de
data/fetcher.py.
"""

import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

from backtesting.arbitragem import LeituraLivro, normalizar_niveis
from data.arbitragem_triangular_store import registrar_ciclos
from data.fetcher import get_exchange
from utils.logger import get_logger

log = get_logger("arbitragem_triangular")

# D1 -- taxa taker spot da Binance, ja verificada nesta sessao
# (config.settings.BACKTEST_FEE_RATE == 0.10%, mesma corretora nas tres
# pernas -- diferente de H15, que soma taxas de corretoras distintas).
CUSTO_TAKER_BINANCE = 0.00100
CUSTO_3_PERNAS = 3 * CUSTO_TAKER_BINANCE

# D2 -- mesmo volume de referencia de H15, para comparabilidade entre as
# duas hipoteses de arbitragem deste registro.
VOLUME_USDT_PADRAO = 10_000.0

# D3 -- reusa o teto de H15 (spec 029/053) por comparabilidade, mesmo
# sendo conservador aqui: as tres pernas sao lidas em paralelo dentro da
# MESMA corretora, entao o intervalo real deveria ficar bem abaixo disso.
TETO_LATENCIA_MS = 2000

# D4 -- mesmo piso de estabilidade de media de H15.
MIN_OBSERVACOES_AGREGACAO = 30

_TOLERANCIA_PREENCHIMENTO = 1e-6


def ler_livro(par: str) -> LeituraLivro:
    """Le o livro de ofertas publico de `par` na Binance (spot, mesma
    instancia cacheada de data.fetcher.get_exchange). Falha nunca levanta
    excecao para o chamador -- vira LeituraLivro(erro=...)."""
    try:
        exchange = get_exchange()
        book = exchange.fetch_order_book(par)
    except Exception as exc:
        log.warning(f"Falha ao ler livro de {par}: {exc}")
        return LeituraLivro(corretora="binance", par=par, instante=time.monotonic(), erro=str(exc))

    return LeituraLivro(
        corretora="binance",
        par=par,
        instante=time.monotonic(),
        bids=normalizar_niveis(book.get("bids")),
        asks=normalizar_niveis(book.get("asks")),
    )


def _comprar(niveis: list[tuple[float, float]], orcamento: float) -> tuple[float, float, float]:
    """Gasta ate `orcamento` (moeda de cotacao da perna) andando os niveis
    de ASK. Devolve (preco_medio, cotacao_gasta, quantidade_obtida)."""
    restante = orcamento
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
        return 0.0, 0.0, 0.0
    return custo_total / qtd_total, custo_total, qtd_total


def _vender(niveis: list[tuple[float, float]], quantidade: float) -> tuple[float, float, float]:
    """Vende ate `quantidade` (moeda base da perna) andando os niveis de
    BID. Devolve (preco_medio, quantidade_vendida, receita_em_cotacao)."""
    restante = quantidade
    receita_total = 0.0
    qtd_total = 0.0
    for preco, qtd in niveis:
        if preco <= 0 or qtd <= 0:
            continue
        consumido = min(restante, qtd)
        receita_total += consumido * preco
        qtd_total += consumido
        restante -= consumido
        if restante <= 0:
            break
    if qtd_total <= 0:
        return 0.0, 0.0, 0.0
    return receita_total / qtd_total, qtd_total, receita_total


def _preenchido(consumido: float, alvo: float) -> bool:
    if alvo <= 0:
        return True
    return consumido >= alvo * (1 - _TOLERANCIA_PREENCHIMENTO)


@dataclass
class CicloTriangular:
    triangulo: str
    direcao: str  # "direto" (cotacao->base->intermediaria->cotacao) ou "inverso"
    volume_usdt: float
    volume_final_usdt: float
    diferencial_bruto_pct: float
    custo_pct: float
    diferencial_liquido_pct: float
    profundidade_suficiente: bool
    estado: str
    intervalo_ms: float = 0.0
    instante_registro: float = field(default_factory=time.time)


def _montar_ciclo(triangulo: str, direcao: str, volume_usdt: float, volume_final: float,
                   profundidade_suficiente: bool, intervalo_ms: float) -> CicloTriangular:
    diferencial_bruto_pct = (volume_final - volume_usdt) / volume_usdt if volume_usdt else 0.0
    diferencial_liquido_pct = diferencial_bruto_pct - CUSTO_3_PERNAS

    if not profundidade_suficiente:
        estado = "profundidade_insuficiente"
    elif intervalo_ms > TETO_LATENCIA_MS:
        estado = "latencia_alta"
    elif diferencial_liquido_pct > 0:
        estado = "oportunidade"
    else:
        estado = "sem_oportunidade"

    return CicloTriangular(
        triangulo=triangulo, direcao=direcao, volume_usdt=volume_usdt,
        volume_final_usdt=volume_final, diferencial_bruto_pct=diferencial_bruto_pct,
        custo_pct=CUSTO_3_PERNAS, diferencial_liquido_pct=diferencial_liquido_pct,
        profundidade_suficiente=profundidade_suficiente, estado=estado, intervalo_ms=intervalo_ms,
    )


def medir_triangulo(
    base: str = "BTC", intermediaria: str = "ETH", cotacao: str = "USDT",
    volume_usdt: float = VOLUME_USDT_PADRAO,
) -> tuple[list[CicloTriangular], list[str]]:
    """Um ciclo de medicao: le os tres livros (base/cotacao,
    intermediaria/base, intermediaria/cotacao) em paralelo e mede as duas
    direcoes possiveis do triangulo.

    Falha de qualquer perna aborta a medicao deste ciclo (diferente de
    H15, onde 15 combinacoes sao independentes -- aqui as tres pernas sao
    o MESMO ciclo, um triangulo com uma perna faltando nao produz medicao
    parcial que faca sentido).
    """
    triangulo = f"{base}-{intermediaria}-{cotacao}"
    par_base_cotacao = f"{base}/{cotacao}"
    par_int_base = f"{intermediaria}/{base}"
    par_int_cotacao = f"{intermediaria}/{cotacao}"

    with ThreadPoolExecutor(max_workers=3) as executor:
        leituras = list(executor.map(ler_livro, (par_base_cotacao, par_int_base, par_int_cotacao)))
    l_base_cot, l_int_base, l_int_cot = leituras

    indisponiveis = [leitura.par for leitura in leituras if not leitura.sucesso]
    if indisponiveis:
        return [], indisponiveis

    intervalo_ms = (max(leitura.instante for leitura in leituras)
                     - min(leitura.instante for leitura in leituras)) * 1000

    # Direto: cotacao -> base -> intermediaria -> cotacao
    _, gasto1, qtd_base = _comprar(l_base_cot.asks, volume_usdt)
    _, gasto2, qtd_int = _comprar(l_int_base.asks, qtd_base)
    _, vendido3, receita = _vender(l_int_cot.bids, qtd_int)
    suficiente_direto = (
        _preenchido(gasto1, volume_usdt)
        and _preenchido(gasto2, qtd_base)
        and _preenchido(vendido3, qtd_int)
    )
    ciclo_direto = _montar_ciclo(triangulo, "direto", volume_usdt, receita,
                                  suficiente_direto, intervalo_ms)

    # Inverso: cotacao -> intermediaria -> base -> cotacao
    _, gasto1i, qtd_int_i = _comprar(l_int_cot.asks, volume_usdt)
    _, vendido2i, qtd_base_i = _vender(l_int_base.bids, qtd_int_i)
    _, vendido3i, receita_i = _vender(l_base_cot.bids, qtd_base_i)
    suficiente_inverso = (
        _preenchido(gasto1i, volume_usdt)
        and _preenchido(vendido2i, qtd_int_i)
        and _preenchido(vendido3i, qtd_base_i)
    )
    ciclo_inverso = _montar_ciclo(triangulo, "inverso", volume_usdt, receita_i,
                                   suficiente_inverso, intervalo_ms)

    ciclos = [ciclo_direto, ciclo_inverso]
    registrar_ciclos(ciclos)
    return ciclos, indisponiveis


_MOTIVO_INEXECUTAVEL = (
    "execucao das tres pernas em sequencia sem garantia de atomicidade -- entre a leitura do "
    "livro e o envio da ordem o preco pode mover, e nenhuma das tres pernas esta implementada (D6)"
)


@dataclass
class RelatorioH22:
    ciclo_atual: list[CicloTriangular]
    indisponiveis: list[str]
    n_observacoes_total: int
    n_observacoes_por_direcao: dict[tuple[str, str], int]
    estado_agregado: str
    executavel_em_producao: bool = False
    motivo_executabilidade: str = _MOTIVO_INEXECUTAVEL


def agregar(ciclo_atual: list[CicloTriangular], observacoes_historico: list[dict]) -> RelatorioH22:
    """Agrega todo o historico persistido (nao so o ciclo atual).
    `estado_agregado` e so descritivo -- nunca aprovado/reprovado (mesmo
    principio de H15/spec 029, FR-010: o veredito exige tempo decorrido)."""
    n_por_direcao: dict[tuple[str, str], int] = {}
    for o in observacoes_historico:
        chave = (o.get("triangulo", ""), o.get("direcao", ""))
        n_por_direcao[chave] = n_por_direcao.get(chave, 0) + 1

    menor_combinacao = min(n_por_direcao.values(), default=0)
    estado_agregado = (
        "amostra_suficiente" if menor_combinacao >= MIN_OBSERVACOES_AGREGACAO else "inconclusivo"
    )

    return RelatorioH22(
        ciclo_atual=ciclo_atual,
        indisponiveis=[],
        n_observacoes_total=len(observacoes_historico),
        n_observacoes_por_direcao=n_por_direcao,
        estado_agregado=estado_agregado,
    )
