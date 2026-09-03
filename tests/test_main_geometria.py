import pytest

import main


def test_geometria_command_is_registered():
    assert "geometria" in main.COMMANDS


def test_fracao_custo_consumida_reproduz_exemplo_ja_publicado_de_h10():
    """Mesma formula ja usada em H10 (registro-de-hipoteses.md linha 586):
    +3,96% com custo, +5,56% sem custo -> custo consome 29% da vantagem
    bruta."""
    assert main._fracao_custo_consumida(com_custo=3.96, sem_custo=5.56) == pytest.approx(0.2878, abs=0.001)


def test_fracao_custo_consumida_e_none_quando_vantagem_bruta_nao_positiva():
    assert main._fracao_custo_consumida(com_custo=-1.0, sem_custo=0.0) is None
    assert main._fracao_custo_consumida(com_custo=-1.0, sem_custo=-2.0) is None
