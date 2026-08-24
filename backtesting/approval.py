from dataclasses import dataclass
from typing import List, Optional, Protocol, Tuple

from backtesting.engine import BacktestResult
from config.settings import EDGE_MIN_TRADES

# Criterios de aprovacao automatica (ROADMAP.md, esbocado na Fase 1), aplicaveis a
# qualquer resultado de backtest de janela unica -- com ou sem split treino/validacao
# (spec 001 US3 usa isto sobre a janela de validacao; spec 002 usa isto direto sobre
# o resultado de edge/multibacktest/scan, que nunca fazem split).
MIN_PROFIT_FACTOR_FOR_APPROVAL = 1.2
MAX_ACCEPTABLE_DRAWDOWN_PCT = 10.0

# Amostra abaixo disso nunca deve dominar o ranking por qualidade, mesmo com
# edge_score alto (ex: 1 trade sortudo com retorno grande) -- mesma protecao que o
# ScanResult.score antigo tinha (`trades < 3` => exclusao dura), perdida quando o
# ranking migrou para edge_score (achado de /code-review high nesta spec).
MIN_TRADES_FOR_RANKING = 3


@dataclass
class ApprovalVerdict:
    status: str  # "aprovado" | "reprovado" | "inconclusivo"
    reasons: List[str]


def evaluate_approval(
    result: Optional[BacktestResult],
    min_trades: int = EDGE_MIN_TRADES,
    min_profit_factor: float = MIN_PROFIT_FACTOR_FOR_APPROVAL,
    max_drawdown_pct: float = MAX_ACCEPTABLE_DRAWDOWN_PCT,
) -> ApprovalVerdict:
    """Aplica os criterios de aprovacao automatica sobre um resultado de backtest
    de janela unica (nunca sobre a janela de treino, quando houver split -- ver
    backtesting/validation.py)."""
    if result is None:
        return ApprovalVerdict(
            status="inconclusivo",
            reasons=["dados insuficientes para uma janela de validacao out-of-sample"],
        )

    # "inconclusivo", nao "reprovado": nada foi provado sobre a estrategia neste
    # par -- o bot simplesmente nunca vai operar ele, porque trading/runner.py
    # descarta precos abaixo de MIN_PRICE_USDT antes de avaliar o sinal.
    # Reprovar daria a entender que a estrategia foi testada e falhou.
    if getattr(result, "below_min_price", False):
        return ApprovalVerdict(
            status="inconclusivo",
            reasons=["preco abaixo de MIN_PRICE_USDT -- o bot nunca opera este par em producao"],
        )

    reasons: List[str] = []
    if result.total_trades < min_trades:
        reasons.append(f"apenas {result.total_trades} trades na validacao (minimo {min_trades})")
    if result.total_return_pct <= result.buy_hold_return_pct:
        reasons.append(
            f"retorno {result.total_return_pct:+.2f}% nao supera buy-and-hold "
            f"{result.buy_hold_return_pct:+.2f}%"
        )
    if result.profit_factor <= min_profit_factor:
        reasons.append(f"profit factor {result.profit_factor:.2f} abaixo do minimo {min_profit_factor}")
    if result.max_drawdown_pct > max_drawdown_pct:
        reasons.append(f"drawdown {result.max_drawdown_pct:.2f}% acima do aceitavel {max_drawdown_pct:.0f}%")

    if reasons:
        return ApprovalVerdict(status="reprovado", reasons=reasons)
    return ApprovalVerdict(status="aprovado", reasons=[])


def diagnose_profile(result: BacktestResult) -> Optional[str]:
    """Diagnostico complementar ao veredito (ROADMAP.md Fase 1.1 item 4): identifica
    o caso de uma estrategia que preserva capital (drawdown baixo, expectativa
    positiva) mas nao acompanha uma alta forte -- diferente de uma estrategia
    simplesmente ruim. So retorna algo quando o padrao "defensivo" e detectado;
    reusa os mesmos limiares ja definidos em evaluate_approval() (nao inventa
    novos numeros "baixo drawdown" divergentes no mesmo relatorio)."""
    is_defensive = (
        result.max_drawdown_pct <= MAX_ACCEPTABLE_DRAWDOWN_PCT
        and result.expectancy > 0
        and result.total_return_pct <= result.buy_hold_return_pct
    )
    if is_defensive:
        return "perfil defensivo: preservou capital, mas capturou pouco da alta"

    # "significativamente acima" = 50% do MODULO do buy-hold acima dele, nao
    # `buy_hold * 1.5` puro -- com buy-hold negativo (ex: bear market, -30%)
    # o multiplicador inverte o limiar (-30*1.5=-45, qualquer perda menor que
    # -45% passaria como "bem acima"), rotulando estrategia perdedora como
    # "agressiva" so por ter perdido menos que o benchmark (achado de
    # /code-review medium).
    aggressive_threshold = result.buy_hold_return_pct + abs(result.buy_hold_return_pct) * 0.5
    is_aggressive = (
        result.max_drawdown_pct > MAX_ACCEPTABLE_DRAWDOWN_PCT
        and result.total_return_pct > aggressive_threshold
    )
    if is_aggressive:
        return "perfil agressivo: retorno bem acima do buy-and-hold as custas de drawdown alto"
    return None


class _Rankable(Protocol):
    edge_score: float
    profit_factor: float
    trades: int


def ranking_key(r: _Rankable) -> Tuple[float, float, int]:
    """Chave de ordenacao por qualidade compartilhada entre `multibacktest` e
    `scan` (`.sort(key=ranking_key, reverse=True)`): edge_score desc, desempate
    por profit_factor e depois por numero de trades. Amostra abaixo de
    `MIN_TRADES_FOR_RANKING` usa `-inf` no lugar do edge_score real, garantindo
    que nunca apareça no topo do ranking só por ter tido sorte numa amostra
    minuscula."""
    effective_score = r.edge_score if r.trades >= MIN_TRADES_FOR_RANKING else float("-inf")
    return (effective_score, r.profit_factor, r.trades)


def verdict_markup(verdict: Optional[ApprovalVerdict]) -> str:
    """Markup Rich para exibir o veredito numa tabela (`multibacktest`/`scan`),
    compartilhado para os dois nao divergirem na cor/texto de cada status."""
    if verdict is None:
        return "-"
    color = {"aprovado": "bright_green", "reprovado": "bright_red", "inconclusivo": "dim cyan"}[verdict.status]
    return f"[{color}]{verdict.status}[/{color}]"
