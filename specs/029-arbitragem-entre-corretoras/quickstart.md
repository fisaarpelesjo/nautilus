# Quickstart — validar H15 (spec 029)

## Pré-requisitos

- Ambiente do projeto já configurado (`pip install -r requirements.txt`).
- Acesso de rede às seis corretoras públicas (`binance`, `bybit`, `okx`,
  `kucoin`, `gate`, `kraken`) — nenhuma chave de API é necessária (FR-013).

## 1. Rodar um ciclo isolado

```bash
python main.py arbitragem
```

Espera-se, em segundos:

- Uma tabela com até 15 combinações de corretoras para `BTC/USDT`.
- Cada linha com diferencial bruto, custo, diferencial líquido, volume
  preenchido e intervalo em ms.
- Estado majoritário esperado: `sem_oportunidade` — a medição preliminar
  (research.md) já mostrou diferencial bruto uma ordem de grandeza abaixo do
  custo mínimo. Ver `custo_desconhecido` só se `TAXA_TOMADOR` estiver
  incompleta; `profundidade_insuficiente` só deveria aparecer para
  `kraken` em volumes maiores que os US$ 10.000 default (D2 já mediu isso).

## 2. Confirmar a persistência por acréscimo

```bash
python main.py arbitragem
wc -l data/arbitragem.jsonl   # ou Get-Content | Measure-Object -Line no PowerShell
python main.py arbitragem
wc -l data/arbitragem.jsonl
```

A segunda contagem MUST ser maior que a primeira — prova direta de FR-008 e
da Acceptance Scenario 1 de US4 ("execuções sucessivas... as observações da
primeira permanecem").

## 3. Confirmar o agregado histórico

Na saída de qualquer execução após a primeira, a seção "Agregado histórico"
MUST mostrar:

- Período coberto com duas datas/horas (primeira e última observação de
  **todo** o arquivo, não só do ciclo atual).
- `N` total maior que o de uma execução isolada.
- `estado_agregado = "inconclusivo"` até `data/arbitragem.jsonl` acumular
  `MIN_OBSERVACOES_AGREGACAO` (30) observações na combinação mais medida —
  o que uma sessão de validação manual não vai atingir sozinha. Isso é
  esperado, não uma falha: é exatamente o que a spec declara em Assumptions.

## 4. Confirmar que uma corretora fora do ar não aborta o ciclo

Sem rede para uma corretora específica (ex.: bloquear `kraken` no
`/etc/hosts` ou firewall local, reversível), rodar de novo:

```bash
python main.py arbitragem
```

Espera-se: a seção "Corretoras indisponíveis" lista `kraken`, as demais
combinações continuam aparecendo normalmente, código de saída `0` (FR-011).

## 5. Confirmar que nenhuma ordem é enviada

Não há passo de validação ativo aqui além de leitura de código: `git grep -n
"create_order\|createOrder" backtesting/arbitragem.py` MUST não retornar nada.
É o mesmo tipo de garantia estática que `test_geometria.py` verifica por AST
contra `import modelo` — `tasks.md` inclui um teste equivalente para
`create_order`.

## 6. Rodar a suite

```bash
pytest tests/test_arbitragem.py -v
```

Cobre: normalização de livro (2 e 3 campos), preço médio de execução com
livro raso, ordem dos estados de `Comparacao`, custo desconhecido nunca
tratado como zero, persistência por acréscimo, agregação e o `estado_agregado`
abaixo/acima de `MIN_OBSERVACOES_AGREGACAO`, e falha isolada por corretora.

## O que este quickstart **não** valida

Não valida se H15 é viável — isso é o veredito que a spec declara fora de
escopo (Assumptions), e que só existe quando a amostra acumulada em
`data/arbitragem.jsonl` atingir o mínimo declarado. Este quickstart valida
que o **instrumento** funciona: mede, classifica, persiste e acumula.
