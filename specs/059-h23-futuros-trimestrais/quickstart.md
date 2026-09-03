# Quickstart: H23 — prêmio de futuros trimestrais (contango) vs. funding perpétuo

## Pré-requisitos

- `.venv` com dependências do projeto instaladas.
- Acesso à Binance para leitura de tickers (endpoint público, sem
  credencial).

## Rodar

```bash
python main.py basis
```

Para cada contrato futuro trimestral USDT-margined disponível (BTC/ETH,
Set/2026 e Dez/2026, únicos 4 existentes): vencimento, dias restantes,
prêmio bruto anualizado, líquido sobre nocional (taxas atuais) e
líquido sobre **capital implantado** (metade do anterior) — comparado
contra o benchmark de 5% a.a. de H8.

Resultado salvo em `reports/basis_<timestamp>.json`.

## Resultado esperado

Ver `research.md`, seção "hipótese declarada antes da medição final".
Contratos de curto prazo podem ficar negativos líquidos (custo fixo
anualizado sobre prazo curto supera o prêmio bruto) — resultado
esperado, não bug.

## Verificação

```bash
pytest tests/test_futures_basis.py tests/test_basis_carry.py -q
```

8 testes: listagem filtra por base/quote/tipo, ordena por vencimento,
cálculo de dias até o vencimento, bruto/líquido/capital-implantado
sobre snapshot sintético, backwardation não quebra, universo avalia
cada contrato listado.
