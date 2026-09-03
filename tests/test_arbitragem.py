"""Testes de H15 -- arbitragem entre corretoras (spec 029).

Ver specs/029-arbitragem-entre-corretoras/{spec,data-model,tasks}.md.
"""


from pathlib import Path

import pytest

from backtesting import arbitragem
from data import arbitragem_store


@pytest.fixture(autouse=True)
def _arbitragem_file_tmp(tmp_path, monkeypatch):
    """Redireciona ARBITRAGEM_FILE para um caminho temporario em todo teste
    deste modulo -- nenhum teste escreve em data/arbitragem.jsonl real."""
    from data import paths as data_paths
    monkeypatch.setattr(data_paths, "ARBITRAGEM_FILE", str(tmp_path / "arbitragem.jsonl"))


# ---------------------------------------------------------------------------
# Foundational: normalizar_niveis (T003)
# ---------------------------------------------------------------------------

def test_normalizar_niveis_dois_campos():
    raw = [[50000.0, 1.5], [50001.0, 2.0]]
    assert arbitragem.normalizar_niveis(raw) == [(50000.0, 1.5), (50001.0, 2.0)]


def test_normalizar_niveis_tres_campos():
    # formato kraken/okx: preco, qtd, instante do nivel -- terceiro descartado
    raw = [[50000.0, 1.5, 1725000000000], [50001.0, 2.0, 1725000000123]]
    assert arbitragem.normalizar_niveis(raw) == [(50000.0, 1.5), (50001.0, 2.0)]


def test_normalizar_niveis_vazio():
    assert arbitragem.normalizar_niveis([]) == []
    assert arbitragem.normalizar_niveis(None) == []


# ---------------------------------------------------------------------------
# Foundational: LeituraLivro / ler_livro (T005)
# ---------------------------------------------------------------------------

class _ExchangeFalso:
    def __init__(self, book=None, falha=False):
        self._book = book
        self._falha = falha
        self.config = {}

    def fetch_order_book(self, par):
        if self._falha:
            raise ConnectionError("timeout simulado")
        return self._book


def test_ler_livro_sucesso(monkeypatch):
    arbitragem.reset_exchange_cache()
    book = {"bids": [[50000.0, 1.0]], "asks": [[50001.0, 1.0]]}
    monkeypatch.setattr(arbitragem, "_get_exchange_publico", lambda c: _ExchangeFalso(book=book))

    leitura = arbitragem.ler_livro("binance", "BTC/USDT")

    assert leitura.sucesso
    assert leitura.corretora == "binance"
    assert leitura.bids == [(50000.0, 1.0)]
    assert leitura.asks == [(50001.0, 1.0)]


def test_ler_livro_falha_nao_levanta_excecao(monkeypatch):
    arbitragem.reset_exchange_cache()
    monkeypatch.setattr(arbitragem, "_get_exchange_publico", lambda c: _ExchangeFalso(falha=True))

    leitura = arbitragem.ler_livro("kraken", "BTC/USDT")

    assert not leitura.sucesso
    assert leitura.erro is not None


def test_get_exchange_publico_nunca_autenticado():
    arbitragem.reset_exchange_cache()
    exchange = arbitragem._get_exchange_publico("binance")
    assert not exchange.apiKey
    assert not exchange.secret


# ---------------------------------------------------------------------------
# US1: preco_medio_execucao (T007)
# ---------------------------------------------------------------------------

def test_preco_medio_execucao_livro_suficiente():
    niveis = [(100.0, 50.0), (101.0, 50.0)]
    preco_medio, volume_preenchido = arbitragem.preco_medio_execucao(niveis, 1000.0)
    assert preco_medio == pytest.approx(100.0)
    assert volume_preenchido == pytest.approx(1000.0)


def test_preco_medio_execucao_livro_raso():
    niveis = [(100.0, 1.0)]  # so 100 USDT de profundidade
    preco_medio, volume_preenchido = arbitragem.preco_medio_execucao(niveis, 1000.0)
    assert volume_preenchido == pytest.approx(100.0)
    assert volume_preenchido < 1000.0


def test_preco_medio_execucao_vazio():
    assert arbitragem.preco_medio_execucao([], 1000.0) == (0.0, 0.0)


def test_preco_medio_execucao_caminha_niveis():
    # primeiro nivel cobre so metade do volume pedido, precisa do segundo
    niveis = [(100.0, 5.0), (102.0, 10.0)]  # 500 USDT + resto no segundo
    preco_medio, volume_preenchido = arbitragem.preco_medio_execucao(niveis, 1000.0)
    assert volume_preenchido == pytest.approx(1000.0)
    assert preco_medio > 100.0  # pior que o topo, caminhou o livro


# ---------------------------------------------------------------------------
# US1: comparar (T008, T009)
# ---------------------------------------------------------------------------

def _leitura(corretora, ask_preco, bid_preco, qtd=100.0, instante=0.0):
    return arbitragem.LeituraLivro(
        corretora=corretora, par="BTC/USDT", instante=instante,
        bids=[(bid_preco, qtd)], asks=[(ask_preco, qtd)],
    )


def test_comparar_diferencial_liquido():
    leitura_a = _leitura("binance", ask_preco=100.0, bid_preco=99.9)
    leitura_b = _leitura("bybit", ask_preco=100.5, bid_preco=100.4)

    c = arbitragem.comparar(leitura_a, leitura_b, volume_usdt=1000.0)

    assert c.corretora_compra == "binance"
    assert c.corretora_venda == "bybit"
    assert c.diferencial_bruto_pct == pytest.approx(0.004)
    assert c.custo_pct == pytest.approx(0.002)
    assert c.diferencial_liquido_pct == pytest.approx(0.002)
    assert c.estado == "oportunidade"
    assert c.volume_preenchido_usdt == pytest.approx(1000.0)


def test_comparar_sem_oportunidade():
    # diferencial bruto positivo mas menor que o custo dos dois lados
    leitura_a = _leitura("binance", ask_preco=100.0, bid_preco=99.9)
    leitura_b = _leitura("bybit", ask_preco=100.05, bid_preco=100.04)

    c = arbitragem.comparar(leitura_a, leitura_b, volume_usdt=1000.0)

    assert c.diferencial_liquido_pct < 0
    assert c.estado == "sem_oportunidade"


def test_comparar_custo_desconhecido_nunca_vira_zero():
    leitura_a = _leitura("binance", ask_preco=100.0, bid_preco=99.9)
    leitura_b = _leitura("corretora_nao_declarada", ask_preco=100.5, bid_preco=100.4)

    c = arbitragem.comparar(leitura_a, leitura_b, volume_usdt=1000.0)

    assert c.estado == "custo_desconhecido"
    assert c.custo_pct is None
    assert c.diferencial_liquido_pct is None


def test_comparar_profundidade_insuficiente():
    leitura_a = _leitura("binance", ask_preco=100.0, bid_preco=99.9, qtd=1.0)  # 100 USDT so
    leitura_b = _leitura("bybit", ask_preco=100.5, bid_preco=100.4, qtd=1.0)

    c = arbitragem.comparar(leitura_a, leitura_b, volume_usdt=10_000.0)

    assert c.estado == "profundidade_insuficiente"
    assert c.volume_preenchido_usdt < 10_000.0


def test_comparar_ordem_estados_custo_precede_profundidade():
    # dispara profundidade insuficiente E custo desconhecido ao mesmo tempo
    leitura_a = _leitura("binance", ask_preco=100.0, bid_preco=99.9, qtd=1.0)
    leitura_b = _leitura("corretora_nao_declarada", ask_preco=100.5, bid_preco=100.4, qtd=1.0)

    c = arbitragem.comparar(leitura_a, leitura_b, volume_usdt=10_000.0)

    assert c.estado == "custo_desconhecido"


# ---------------------------------------------------------------------------
# US1: medir_ciclo (T013) -- falha isolada, FR-011
# ---------------------------------------------------------------------------

def test_medir_ciclo_falha_isolada_nao_aborta(monkeypatch):
    def _ler_livro_falso(corretora, par):
        if corretora == "kraken":
            return arbitragem.LeituraLivro(corretora=corretora, par=par, instante=0.0, erro="falha simulada")
        return _leitura(corretora, ask_preco=100.0, bid_preco=99.9, instante=0.0)

    monkeypatch.setattr(arbitragem, "ler_livro", _ler_livro_falso)

    comparacoes, indisponiveis, pares_recusados = arbitragem.medir_ciclo("BTC/USDT", volume_usdt=1000.0)

    assert indisponiveis == ["kraken"]
    corretoras_nas_comparacoes = {c.corretora_compra for c in comparacoes} | {c.corretora_venda for c in comparacoes}
    assert "kraken" not in corretoras_nas_comparacoes
    from math import comb
    assert len(comparacoes) == comb(len(arbitragem.CORRETORAS) - 1, 2)
    assert pares_recusados == []


# ==================================== spec 053 (H15 leitura paralela)

def test_medir_ciclo_le_as_corretoras_em_paralelo(monkeypatch):
    """M15 (docs/research/registro-de-hipoteses.md S5): leitura sequencial
    fazia o intervalo entre a primeira e a ultima corretora ultrapassar
    sozinho o teto de latencia. Com leitura paralela, seis corretoras que
    demoram ~0,2s cada MUST completar perto de 0,2s no total, nao de 1,2s
    (6x0,2s) que a versao sequencial levaria."""
    import time

    ATRASO = 0.2

    def _ler_livro_lento(corretora, par):
        time.sleep(ATRASO)
        return _leitura(corretora, ask_preco=100.0, bid_preco=99.9, instante=time.monotonic())

    monkeypatch.setattr(arbitragem, "ler_livro", _ler_livro_lento)

    inicio = time.monotonic()
    arbitragem.medir_ciclo("BTC/USDT", volume_usdt=1000.0)
    duracao = time.monotonic() - inicio

    n = len(arbitragem.CORRETORAS)
    assert duracao < ATRASO * (n / 2)  # bem abaixo do tempo sequencial (n * ATRASO)


def test_medir_ciclo_falha_isolada_nao_aborta_sob_paralelismo(monkeypatch):
    """Regressao de FR-002/FR-011: uma corretora falhando nao pode afetar
    as demais nem abortar o ciclo, mesmo com a leitura paralela."""
    def _ler_livro_falso(corretora, par):
        if corretora == "kraken":
            return arbitragem.LeituraLivro(corretora=corretora, par=par, instante=0.0, erro="falha simulada")
        return _leitura(corretora, ask_preco=100.0, bid_preco=99.9, instante=0.0)

    monkeypatch.setattr(arbitragem, "ler_livro", _ler_livro_falso)

    comparacoes, indisponiveis, pares_recusados = arbitragem.medir_ciclo("BTC/USDT", volume_usdt=1000.0)

    assert indisponiveis == ["kraken"]
    from math import comb
    assert len(comparacoes) == comb(len(arbitragem.CORRETORAS) - 1, 2)


# ---------------------------------------------------------------------------
# US2: mesma_cotacao (T016, T017)
# ---------------------------------------------------------------------------

def test_mesma_cotacao_compativel():
    leitura_a = arbitragem.LeituraLivro(corretora="binance", par="BTC/USDT", instante=0.0)
    leitura_b = arbitragem.LeituraLivro(corretora="kraken", par="BTC/USDT", instante=0.0)
    compativel, motivo = arbitragem.mesma_cotacao(leitura_a, leitura_b)
    assert compativel
    assert motivo is None


def test_mesma_cotacao_incompativel():
    leitura_a = arbitragem.LeituraLivro(corretora="binance", par="BTC/USDT", instante=0.0)
    leitura_b = arbitragem.LeituraLivro(corretora="kraken", par="BTC/USD", instante=0.0)
    compativel, motivo = arbitragem.mesma_cotacao(leitura_a, leitura_b)
    assert not compativel
    assert motivo is not None
    assert "USDT" in motivo and "USD" in motivo


def test_medir_ciclo_recusa_cotacao_diferente(monkeypatch):
    def _ler_livro_falso(corretora, par):
        cotacao = "USD" if corretora == "kraken" else "USDT"
        return arbitragem.LeituraLivro(
            corretora=corretora, par=f"BTC/{cotacao}", instante=0.0,
            bids=[(99.9, 100.0)], asks=[(100.0, 100.0)],
        )

    monkeypatch.setattr(arbitragem, "ler_livro", _ler_livro_falso)

    comparacoes, indisponiveis, pares_recusados = arbitragem.medir_ciclo("BTC/USDT", volume_usdt=1000.0)

    corretoras_nas_comparacoes = {c.corretora_compra for c in comparacoes} | {c.corretora_venda for c in comparacoes}
    assert "kraken" not in corretoras_nas_comparacoes
    assert any("kraken" in (a, b) for a, b, _motivo in pares_recusados)


# ---------------------------------------------------------------------------
# US3: latencia (T021, T022)
# ---------------------------------------------------------------------------

def test_comparar_calcula_intervalo_ms():
    leitura_a = _leitura("binance", ask_preco=100.0, bid_preco=99.9, instante=10.000)
    leitura_b = _leitura("bybit", ask_preco=100.5, bid_preco=100.4, instante=10.342)

    c = arbitragem.comparar(leitura_a, leitura_b, volume_usdt=1000.0)

    assert c.intervalo_ms == pytest.approx(342.0, abs=0.01)


def test_comparar_latencia_alta_precede_oportunidade():
    # diferencial liquido seria positivo, mas o intervalo estoura o teto
    leitura_a = _leitura("binance", ask_preco=100.0, bid_preco=99.9, instante=0.0)
    intervalo_s = (arbitragem.TETO_LATENCIA_MS + 1) / 1000
    leitura_b = _leitura("bybit", ask_preco=100.5, bid_preco=100.4, instante=intervalo_s)

    c = arbitragem.comparar(leitura_a, leitura_b, volume_usdt=1000.0)

    assert c.diferencial_liquido_pct is not None and c.diferencial_liquido_pct > 0
    assert c.estado == "latencia_alta"


def test_comparar_latencia_dentro_do_teto_nao_bloqueia():
    leitura_a = _leitura("binance", ask_preco=100.0, bid_preco=99.9, instante=0.0)
    leitura_b = _leitura("bybit", ask_preco=100.5, bid_preco=100.4, instante=0.5)

    c = arbitragem.comparar(leitura_a, leitura_b, volume_usdt=1000.0)

    assert c.estado == "oportunidade"


# ---------------------------------------------------------------------------
# US4: data/arbitragem_store.py (T025, T026)
# ---------------------------------------------------------------------------

def test_registrar_observacoes_acrescenta_sem_sobrescrever():
    c1 = arbitragem.comparar(_leitura("binance", 100.0, 99.9), _leitura("bybit", 100.5, 100.4))
    c2 = arbitragem.comparar(_leitura("okx", 100.0, 99.9), _leitura("gate", 100.5, 100.4))

    arbitragem_store.registrar_observacoes([c1])
    arbitragem_store.registrar_observacoes([c2])

    observacoes = arbitragem_store.carregar_observacoes()
    assert len(observacoes) == 2


def test_carregar_observacoes_descarta_linha_parcial():
    from data import paths as data_paths

    c1 = arbitragem.comparar(_leitura("binance", 100.0, 99.9), _leitura("bybit", 100.5, 100.4))
    arbitragem_store.registrar_observacoes([c1])
    with open(data_paths.ARBITRAGEM_FILE, "a", encoding="utf-8") as f:
        f.write('{"corretora_compra": "gate", "estado": "oportuni')  # linha parcial, sem \n

    observacoes = arbitragem_store.carregar_observacoes()
    assert len(observacoes) == 1


def test_carregar_observacoes_arquivo_inexistente():
    assert arbitragem_store.carregar_observacoes() == []


# ---------------------------------------------------------------------------
# US4: agregar() (T027)
# ---------------------------------------------------------------------------

def _observacao(corretora_compra, corretora_venda, instante_registro):
    return {"corretora_compra": corretora_compra, "corretora_venda": corretora_venda,
            "instante_registro": instante_registro, "estado": "sem_oportunidade"}


def test_agregar_periodo_e_contagem():
    historico = [
        _observacao("binance", "bybit", 100.0),
        _observacao("binance", "bybit", 200.0),
        _observacao("okx", "gate", 150.0),
    ]

    r = arbitragem.agregar([], [], [], historico)

    assert r.periodo_coberto == (100.0, 200.0)
    assert r.n_observacoes_total == 3
    assert r.n_observacoes_por_combinacao[tuple(sorted(("binance", "bybit")))] == 2
    assert r.n_observacoes_por_combinacao[tuple(sorted(("okx", "gate")))] == 1


def test_agregar_inconclusivo_abaixo_do_minimo():
    historico = [_observacao("binance", "bybit", float(i)) for i in range(arbitragem.MIN_OBSERVACOES_AGREGACAO - 1)]
    r = arbitragem.agregar([], [], [], historico)
    assert r.estado_agregado == "inconclusivo"


def test_agregar_amostra_suficiente_no_minimo():
    historico = [_observacao("binance", "bybit", float(i)) for i in range(arbitragem.MIN_OBSERVACOES_AGREGACAO)]
    r = arbitragem.agregar([], [], [], historico)
    assert r.estado_agregado == "amostra_suficiente"


def test_agregar_nunca_tem_campo_de_veredito():
    # RelatorioH15 nao pode ter aprovada/reprovada -- Assumptions da spec
    r = arbitragem.agregar([], [], [], [])
    assert not hasattr(r, "aprovada")
    assert not hasattr(r, "reprovada")
    assert r.estado_agregado in ("inconclusivo", "amostra_suficiente")


def test_agregar_historico_vazio():
    r = arbitragem.agregar([], [], [], [])
    assert r.periodo_coberto is None
    assert r.n_observacoes_total == 0
    assert r.estado_agregado == "inconclusivo"


def test_agregar_executabilidade_sempre_falsa():
    r = arbitragem.agregar([], [], [], [])
    assert r.executavel_em_producao is False
    assert r.motivo_executabilidade  # nunca vazio


# ---------------------------------------------------------------------------
# US4: integracao medir_ciclo -> persistencia (T030)
# ---------------------------------------------------------------------------

def test_medir_ciclo_persiste_comparacoes(monkeypatch):
    monkeypatch.setattr(arbitragem, "ler_livro", lambda corretora, par: _leitura(corretora, 100.0, 99.9))

    comparacoes, _indisponiveis, _recusados = arbitragem.medir_ciclo("BTC/USDT", volume_usdt=1000.0)

    observacoes = arbitragem_store.carregar_observacoes()
    assert len(observacoes) == len(comparacoes)


def test_medir_ciclo_duas_execucoes_acumulam(monkeypatch):
    monkeypatch.setattr(arbitragem, "ler_livro", lambda corretora, par: _leitura(corretora, 100.0, 99.9))

    comparacoes_1, _, _ = arbitragem.medir_ciclo("BTC/USDT", volume_usdt=1000.0)
    comparacoes_2, _, _ = arbitragem.medir_ciclo("BTC/USDT", volume_usdt=1000.0)

    observacoes = arbitragem_store.carregar_observacoes()
    assert len(observacoes) == len(comparacoes_1) + len(comparacoes_2)


# ---------------------------------------------------------------------------
# Polish: guardas estruturais (T033, T034)
# ---------------------------------------------------------------------------

def test_nunca_envia_ordem():
    """FR-012 -- H15 e medicao, nunca execucao. Guarda textual, mesmo
    espirito da guarda AST de tests/test_geometria.py contra `import modelo`."""
    for caminho in ("backtesting/arbitragem.py", "data/arbitragem_store.py"):
        texto = Path(caminho).read_text(encoding="utf-8")
        assert "create_order" not in texto
        assert "createOrder" not in texto


def test_ler_livro_nunca_passa_credenciais(monkeypatch):
    """FR-013 -- nenhuma das seis corretoras exige chave de API."""
    capturado = {}

    class _ExchangeClasseFalsa:
        def __init__(self, config):
            capturado["config"] = config
            self.apiKey = None
            self.secret = None

        def fetch_order_book(self, par):
            return {"bids": [], "asks": []}

    arbitragem.reset_exchange_cache()
    monkeypatch.setattr(arbitragem.ccxt, "binance", _ExchangeClasseFalsa)

    arbitragem.ler_livro("binance", "BTC/USDT")

    assert "apiKey" not in capturado["config"]
    assert "secret" not in capturado["config"]
