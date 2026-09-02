# Quickstart — validar a spec 030

## Pré-requisitos

- Ambiente do projeto já configurado (`pip install -r requirements.txt`).

## 1. Rodar a suite existente (regressão)

```bash
pytest tests/test_liquidity.py -v
```

Todos os testes já existentes (`test_check_liquidity_blocks_on_high_spread`,
`test_check_liquidity_blocks_on_low_depth`,
`test_check_liquidity_treats_network_failure_as_blocked`,
`test_check_liquidity_blocks_on_corrupted_best_ask`,
`test_check_liquidity_approves_within_limits`) MUST continuar passando sem
alteração — nenhum deles usa profundidade concentrada fora do desvio de
preço aceito, então nenhum deve mudar de resultado (US2).

## 2. Confirmar o gap fecha (US1)

Um teste novo constrói um book sintético com profundidade total acima do
requisito, mas concentrada em níveis distantes do melhor ask (replicando o
padrão medido em `research.md` para ORCA/USDT: ~90% da soma bruta fora de
0,5%). Espera-se:

```bash
pytest tests/test_liquidity.py -k phantom -v
```

`approved is False`, com motivo distinguível do motivo de spread.

## 3. Confirmar contra dados reais (opcional, validação manual)

```bash
python - <<'EOF'
from execution.liquidity import check_liquidity
for par in ("ORCA/USDT", "COW/USDT", "HEMI/USDT", "ROBO/USDT"):
    r = check_liquidity(par, order_size_usdt=100.0)
    print(par, r.approved, r.depth_usdt, r.reason)
EOF
```

Ao tamanho de ordem atual (`MAX_ORDER_SIZE_USDT = 100`, default), a decisão
MUST ser idêntica à de antes da mudança (research.md, medição de
divergência: 0/88 a US$ 100). Para ver a divergência real, repita com
`order_size_usdt=10000.0` num dos quatro pares citados no research.md.

## 4. Rodar a suite completa

```bash
pytest -q
```

Nenhuma regressão fora de `test_liquidity.py` — a mudança é local a uma
função, sem novo import em `trading/position_lifecycle.py` ou
`execution/order_manager.py`.

## O que este quickstart não valida

Não valida em `TRADING_MODE=live` — o repositório roda só em paper (VPS).
Confirmar em paper antes de qualquer consideração de live é responsabilidade
operacional já coberta pelo Princípio I da constitution, não desta spec.
