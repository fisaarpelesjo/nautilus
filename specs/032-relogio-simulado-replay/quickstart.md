# Quickstart — validar a spec 032

## Pré-requisitos

- Ambiente do projeto já configurado (`pip install -r requirements.txt`).

## 1. Confirmar zero mudança fora do replay (regressão, sem rede)

```bash
pytest tests/test_order_manager_state.py tests/test_order_manager_paper.py -v
```

(ou os arquivos equivalentes que já cobrem cooldown/drawdown/circuit
breaker) — todos MUST continuar passando sem alteração. Nenhum usa
`_simulated_now`, então `_now()` é `datetime.now()` em todos.

## 2. Rodar os testes novos de `_now()` (sem rede)

```bash
pytest -k "_now or simulated_now" -v
```

Cobre: `_now()` sem `_simulated_now` setado é indistinguível de
`datetime.now()` (dentro de uma margem de milissegundos); com
`_simulated_now` setado, `_now()` retorna exatamente esse valor.

## 3. Rodar os testes de replay (sem rede, mockado)

```bash
pytest tests/test_replay.py -v
```

Cobre: um cooldown ativado num candle simulado vence quando candles
subsequentes avançam o tempo simulado além de `COOLDOWN_HOURS`, mesmo que
a execução real do teste leve milissegundos; `check_circuit_breaker_timeout`
é chamado a cada ciclo simulado quando o breaker está ativo; ao sair do
ambiente isolado, `order_manager._simulated_now` volta a `None`.

## 4. Confirmar contra um replay real (opcional)

```bash
python main.py replay BTC/USDT
```

Inspecionar o relatório: nenhuma mudança visível no resultado a menos que
o histórico simulado atravesse um cooldown/período/timeout — nesse caso, o
comportamento passa a refletir o tempo do candle, não a duração real da
execução do comando (que leva segundos).

## 5. Rodar a suite completa

```bash
pytest -q
```

Nenhuma regressão fora de `execution/order_manager.py` e
`trading/replay.py`.

## O que este quickstart não valida

Não muda nem valida `TRADING_MODE=live`/`paper` — a garantia central desta
spec (FR-002) é que esses modos permanecem bit a bit idênticos, verificado
pelos testes do passo 1, não por uma execução manual separada.
