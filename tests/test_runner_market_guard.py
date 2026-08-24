"""Guarda de mercado na inicializacao do bot (spec 023, T012 / FR-007).

O caminho de execucao so sabe operar cripto (Binance Spot, conforme a
Constituicao). Um simbolo de mercado sem execucao implementada nao pode chegar
ao loop -- e o mesmo padrao que deixou LUNC/USDT inerte por 8 dias em PAIRS
(spec 021): o simbolo parecia aceito e nunca operava de verdade. A diferenca e
que ali o bot seguia rodando em silencio; aqui ele MUST recusar em voz alta.
"""
import pytest

from trading import runner


def test_aceita_lista_so_de_cripto():
    # Caminho feliz: nada muda para quem opera cripto (FR-006).
    runner.assert_pares_operaveis(["BTC/USDT", "ETH/USDT", "SOL/USDT"])


def test_recusa_simbolo_de_mercado_sem_execucao():
    with pytest.raises(ValueError) as exc:
        runner.assert_pares_operaveis(["BTC/USDT", "AAPL"])

    msg = str(exc.value)
    assert "AAPL" in msg, "a mensagem MUST nomear o simbolo problematico"
    assert "stocks_us" in msg, "a mensagem MUST nomear o mercado sem execucao"


@pytest.mark.parametrize("simbolo", ["AAPL", "PETR4.SA", "EURUSD=X", "ES=F", "^GSPC"])
def test_recusa_cada_mercado_nao_operavel(simbolo):
    with pytest.raises(ValueError):
        runner.assert_pares_operaveis([simbolo])


def test_recusa_simbolo_nao_resolvivel():
    # Nao resolver para nenhum mercado tambem MUST bloquear -- aceitar seria
    # deixar passar um simbolo que nenhuma fonte sabe buscar.
    with pytest.raises(ValueError):
        runner.assert_pares_operaveis(["!!!"])


def test_lista_todos_os_problematicos_de_uma_vez():
    # Reportar so o primeiro forcaria o operador a descobrir um por vez.
    with pytest.raises(ValueError) as exc:
        runner.assert_pares_operaveis(["AAPL", "BTC/USDT", "EURUSD=X"])

    msg = str(exc.value)
    assert "AAPL" in msg
    assert "EURUSD=X" in msg
