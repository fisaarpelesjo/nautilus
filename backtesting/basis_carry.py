"""H23 -- prêmio de futuros com vencimento fixo (contango) vs. funding
perpétuo (H8). `specs/059-h23-futuros-trimestrais/research.md` declara
antes de medir:

D1 (universo): só BTC/USDT e ETH/USDT têm contrato futuro trimestral
USDT-margined na Binance (verificado 2026-09-03) -- universo pequeno,
não escolhido: é o universo real disponível.

D2 (instantâneo, não série histórica): diferente de funding rate
(histórico contínuo via endpoint dedicado), um contrato trimestral
vencido não tem preço consultável depois do vencimento -- esta medição
é um retrato do prêmio HOJE para os contratos hoje listados, não uma
série de 1 ano como H8. Limitação declarada, não escondida.

D3 (custo e capital): mesma fórmula de custo/eficiência de capital de
H8 (`backtesting/funding_carry.py`, D1/D3) -- reusa
`CUSTO_ABERTURA_FECHAMENTO` (4 pernas: abre spot+futuro, fecha
spot+futuro) sem duplicar a constante; capital implantado = metade do
líquido sobre nocional (sem alavancagem, mesma lógica de H8).

D4 (benchmark): mesmo piso de 5% a.a. de H8 (`BENCHMARK_RENDA_FIXA_AA`,
reusado sem alteração -- mesma pergunta de custo de oportunidade).
"""
from dataclasses import dataclass
from typing import List, Sequence

from backtesting.funding_carry import BENCHMARK_RENDA_FIXA_AA, CUSTO_ABERTURA_FECHAMENTO
from data.futures_basis import fetch_basis_snapshot, listar_contratos_trimestrais


@dataclass
class ResultadoBasisContrato:
    par: str
    symbol: str
    expiry_datetime: str
    dias_ate_vencimento: float
    basis_bruto_aa: float
    basis_liquido_aa_nocional: float
    basis_liquido_aa_capital_implantado: float
    supera_benchmark: bool


def avaliar_contrato(contrato: dict) -> ResultadoBasisContrato:
    snap = fetch_basis_snapshot(contrato)
    dias = snap["dias_ate_vencimento"]
    basis_pct = (snap["preco_futuro"] - snap["preco_spot"]) / snap["preco_spot"]

    fator_anual = 365.0 / dias if dias > 0 else 0.0
    bruto_aa = basis_pct * fator_anual
    liquido_aa_nocional = bruto_aa - CUSTO_ABERTURA_FECHAMENTO * fator_anual
    liquido_aa_capital_implantado = liquido_aa_nocional / 2.0

    return ResultadoBasisContrato(
        par=snap["par"], symbol=snap["symbol"], expiry_datetime=snap["expiry_datetime"],
        dias_ate_vencimento=dias, basis_bruto_aa=bruto_aa,
        basis_liquido_aa_nocional=liquido_aa_nocional,
        basis_liquido_aa_capital_implantado=liquido_aa_capital_implantado,
        supera_benchmark=liquido_aa_capital_implantado > BENCHMARK_RENDA_FIXA_AA,
    )


def avaliar_universo(bases: Sequence[str] = ("BTC", "ETH")) -> List[ResultadoBasisContrato]:
    contratos = listar_contratos_trimestrais(bases=bases)
    return [avaliar_contrato(c) for c in contratos]
