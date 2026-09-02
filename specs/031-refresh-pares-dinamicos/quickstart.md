# Quickstart — validar a spec 031

## Pré-requisitos

- Ambiente do projeto já configurado (`pip install -r requirements.txt`).

## 1. Rodar a suite nova (unitária, sem rede)

```bash
pytest tests/test_runner_dynamic_pairs_refresh.py -v
```

Cobre, com `_FakeManager`/seletor mockado (mesmo padrão de
`tests/test_runner_reconciliation.py`):

- Refresh muda a lista quando o seletor retorna candidatos diferentes.
- **Um símbolo com posição aberta simulada nunca sai de `nova_lista`**, mesmo
  quando o seletor mockado não o inclui — o teste mais importante desta spec
  (FR-002/US2).
- Falha do seletor (exceção mockada) preserva a lista vigente.
- Evento `dynamic_pairs_refreshed` é gravado com `added`/`removed`/
  `kept_for_open_position` corretos, inclusive quando nada muda.

## 2. Confirmar que `DYNAMIC_PAIRS_ENABLED=false` continua inerte

```bash
pytest tests/test_runner_dynamic_pairs_refresh.py -k disabled -v
```

Com a flag desligada (default, config atual do bot), nenhuma chamada a
`select_dynamic_pairs()` deve acontecer — `active_pairs` permanece `PAIRS`
por todo o tempo de execução.

## 3. Validação manual do custo medido (opcional)

```bash
python - <<'EOF'
import time
from market.selector import select_dynamic_pairs
t0 = time.monotonic()
select_dynamic_pairs()
print(f"{time.monotonic() - t0:.1f}s")
EOF
```

Espera-se algo na faixa medida em `research.md` (~36s neste ambiente,
2026-09-02) — confirma que `DYNAMIC_PAIRS_REFRESH_CYCLES=1440` (~24h) é a
ordem de grandeza certa, não uma unidade errada por um fator de 60 ou 3600.

## 4. Rodar a suite completa

```bash
pytest -q
```

Nenhuma regressão fora do arquivo novo — `market/selector.py` não é
alterado, e `_load_active_pairs()` continua sendo chamada exatamente como
hoje no boot.

## O que este quickstart não valida

Não roda o bot de ponta a ponta por 24h reais para observar um refresh
acontecer em produção — isso é validação operacional (paper mode na VPS),
fora do escopo de uma suite automatizada. O quickstart prova que a função de
refresh e a guarda de posição aberta funcionam corretamente de forma
isolada e determinística.
