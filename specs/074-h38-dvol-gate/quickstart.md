# Quickstart: H38 — Gate por volatilidade implícita (Deribit DVOL)

## Pré-requisitos

- `.venv` com dependências do projeto instaladas.
- Acesso à Binance para `fetch_ohlcv` e à Deribit (`www.deribit.com`) para
  o DVOL — API pública, sem chave.

## Rodar

```bash
python main.py dvolgate
```

Sobre `UNIVERSO_H11` (mesmo universo de H27), reconstrói a população de
eventos de entrada do sinal primário (EMA/RSI) já usada por H27, divide
por nível de DVOL (BTC) no momento do evento (decil mais alto vs. resto),
e imprime a razão alvo/stop e o status de significância de cada subgrupo,
junto do número já publicado de H27 para comparação.

Resultado salvo em `reports/dvol_gate_<timestamp>.json`.

## Resultado esperado

Ver `research.md`, seção "Hipótese declarada antes de medir". Dado que a
população de partida (H27, n=740) já está quase no empate, a leitura mais
provável é precondição não atendida — mas a comparação direta entre os
dois subgrupos decide, não a expectativa.

## Verificação

```bash
pytest tests/test_dvol_gate.py -q
```

Cobre: `fetch_dvol_history` nunca devolve sucesso silencioso em falha,
decil calibrado sobre a própria série de DVOL, alinhamento causal D-1,
evento sem DVOL alinhável é excluído (nunca presumido), `avaliar_precondicao_dvol`
funciona com fetchers mockados (sem rede), par sem evento com DVOL é
pulado sem abortar os demais.
