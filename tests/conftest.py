"""Isolamento de escrita em disco para a suite de testes.

Motivacao (2026-09-01): rodar `pytest` gravava 73 linhas em
`logs/events-YYYY-MM-DD.jsonl` do diretorio real. O log operacional do bot em
paper mode passou a conter `live_order_error`, `live_order_opened`,
`circuit_breaker_triggered` e `reconciliation_mismatch` -- eventos que nunca
aconteceram, vindos de fixtures de teste.

O custo disso nao e cosmetico: o log de eventos e a ferramenta de diagnostico
operacional, e um log que mistura producao com teste faz o operador investigar
falha que nao existe. Aconteceu exatamente isso durante a analise do bot.

Os arquivos de trading (`data/trades.csv`, `data/state.json`) ja estavam
protegidos -- verificado por md5 antes e depois da suite, sem alteracao. Mesmo
assim o redirecionamento cobre `data/` tambem, porque a protecao atual depende
de cada teste lembrar de isolar o proprio caminho, e um teste novo que esqueca
escreveria no estado real do bot em producao.
"""
import pytest


@pytest.fixture(autouse=True)
def isolar_escrita_em_disco(tmp_path, monkeypatch):
    """Redireciona toda escrita de log e estado para um diretorio temporario.

    `autouse` de proposito: a protecao nao pode depender de o autor do teste
    lembrar de pedi-la. Um teste novo que grave em disco fica isolado sozinho.
    """
    # Sob um subdiretorio proprio, nao na raiz do tmp_path: varios testes usam
    # o tmp_path deles para montar "data/" e "logs/" a mao, e ocupar esses
    # nomes na raiz faria a fixture colidir com o teste que ela deveria proteger.
    base = tmp_path / "_isolado"
    logs = base / "logs"
    dados = base / "data"
    logs.mkdir(parents=True, exist_ok=True)
    (dados / "ohlcv").mkdir(parents=True, exist_ok=True)

    # utils.logger le LOG_DIR do global no momento da chamada, entao o patch
    # pega tambem as chamadas ja compiladas.
    monkeypatch.setattr("utils.logger.LOG_DIR", str(logs), raising=False)

    # data.paths: cobre quem le o modulo em tempo de chamada. Quem fez
    # `from data.paths import X` no topo capturou o valor antigo e continua
    # responsavel pelo proprio isolamento -- por isso os testes existentes que
    # ja monkeypatcham seus caminhos seguem funcionando sem alteracao.
    for nome, valor in (
        ("TRADES_FILE", dados / "trades.csv"),
        ("SIGNALS_FILE", dados / "signals.csv"),
        ("DECISIONS_FILE", dados / "decisions.csv"),
        ("STATE_FILE", dados / "state.json"),
        ("KILLSWITCH_FILE", dados / "killswitch.json"),
        ("OHLCV_DIR", dados / "ohlcv"),
    ):
        monkeypatch.setattr(f"data.paths.{nome}", str(valor), raising=False)

    yield
