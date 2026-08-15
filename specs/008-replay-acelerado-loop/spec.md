# Feature Specification: Replay Acelerado do Loop Real

**Feature Branch**: `008-replay-acelerado-loop`

**Created**: 2026-08-15

**Status**: Draft

**Input**: User description: "Replay acelerado do loop real do bot contra dados históricos, para
fechar parte do gap de forward test (ROADMAP.md Fase 5 itens 1 e 4) sem exigir o operador rodar o
bot em paper mode por semanas. Motor de replay que itera candle a candle sobre histórico público
chamando as MESMAS funções de decisão usadas pelo bot real (`handle_entry_candidate`,
`handle_open_position`), não a simulação simplificada de `backtesting/engine.py`. Segurança é o
requisito central: o replay MUST NUNCA tocar `data/state.json`/`data/trades.csv`/`data/signals.csv`/
`data/decisions.csv` reais do bot — roda inteiramente isolado. Ao final, compara contra um backtest
simples do mesmo período, reportando divergências. Novo comando `python main.py replay <PAR>`."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Rodar o caminho de decisão real contra histórico, sem tocar o estado real do bot (Priority: P1) 🎯 MVP

Como operador do bot, eu quero rodar o motor de decisão real (o mesmo código que roda no loop de
produção) contra um histórico de candles público, para ver como o bot teria se comportado de
verdade — não a versão simplificada do backtest — sem esperar semanas de operação paper real e sem
nenhum risco de corromper o estado real do bot.

**Why this priority**: É o requisito de segurança inegociável (constitution Principle I) e a base de
tudo o mais nesta spec — sem isolamento garantido, nenhuma outra capacidade pode existir com
segurança.

**Independent Test**: Rodar o replay para um par com histórico suficiente, e confirmar (a) que
produz uma lista de trades coerente usando o caminho de decisão real, e (b) que `data/state.json`,
`data/trades.csv`, `data/signals.csv` e `data/decisions.csv` reais permanecem byte a byte
idênticos ao estado anterior à execução.

**Acceptance Scenarios**:

1. **Given** um par com histórico suficiente de candles públicos, **When** o replay roda,
   **Then** ele produz uma sequência de decisões (entradas, saídas, bloqueios) usando as mesmas
   funções (`handle_entry_candidate`, `handle_open_position`) já usadas pelo loop de produção.
2. **Given** o replay em execução, **When** ele termina, **Then** nenhum arquivo real de estado do
   bot (`data/state.json`, `data/trades.csv`, `data/signals.csv`, `data/decisions.csv`) foi
   modificado — o replay usa armazenamento próprio, isolado, descartável.
3. **Given** uma falha inesperada durante o replay (ex: exceção em uma condição de borda),
   **When** ela ocorre, **Then** o isolamento dos arquivos reais MUST se manter — nenhum caminho de
   erro pode escrever no estado real como efeito colateral.

---

### User Story 2 - Ver onde o comportamento real diverge do backtest simplificado (Priority: P2)

Como operador do bot, eu quero comparar o resultado do replay (caminho de decisão real) contra um
backtest simples do mesmo par/período, para identificar se e onde a simulação simplificada do
backtest diverge do que o bot realmente faria em produção — o próprio propósito do item "comparar
paper vs backtest" do `ROADMAP.md`, sem depender de histórico de operação paper real.

**Why this priority**: Só tem valor depois que o replay em si (US1) existe e é seguro — é a camada
de análise sobre o resultado bruto do replay.

**Independent Test**: Rodar o replay e um backtest simples para o mesmo par/período, e confirmar que
o relatório final mostra as duas listas de trades lado a lado com as divergências (número de trades,
timing de entrada/saída, motivo de bloqueio) destacadas.

**Acceptance Scenarios**:

1. **Given** o resultado do replay e um backtest do mesmo par/período, **When** o relatório de
   comparação é gerado, **Then** ele mostra número de trades de cada lado, diferença de retorno, e
   pelo menos uma explicação textual para divergências relevantes (ex: "backtest não modela cooldown
   de reentrada").
2. **Given** replay e backtest produzem exatamente os mesmos trades, **When** o relatório é gerado,
   **Then** ele indica claramente que não houve divergência relevante, sem inventar diferenças.

---

### Edge Cases

- O que acontece se o replay for iniciado com `TRADING_MODE=live` no ambiente? → O replay MUST
  ignorar `TRADING_MODE` e sempre operar como simulação isolada (paper), nunca tentar enviar uma
  ordem real — mesmo com live configurado no `.env` para o bot de produção.
- O que acontece se o histórico disponível for insuficiente para o warmup dos indicadores? → Mesmo
  tratamento já usado em outras partes do sistema para dados insuficientes: reportado explicitamente,
  não um erro não tratado.
- O que acontece se MTF precisar buscar um timeframe de confirmação durante o replay? → Usa dados
  públicos reais (mesma função já usada no backtest/produção) — não há risco de estado, só leitura de
  mercado público.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST executar o caminho de decisão real (`handle_entry_candidate`,
  `handle_open_position`, já existentes em `trading/position_lifecycle.py`) candle a candle sobre um
  histórico de dados públicos, sem esperar tempo real passar entre ciclos.
- **FR-002**: O sistema MUST NUNCA ler ou escrever nos arquivos reais de estado do bot
  (`data/state.json`, `data/trades.csv`, `data/signals.csv`, `data/decisions.csv`) durante um
  replay, mesmo em caso de erro.
- **FR-003**: O sistema MUST NUNCA enviar uma ordem real a uma exchange durante um replay,
  independente do valor de `TRADING_MODE` no ambiente.
- **FR-004**: O sistema MUST produzir um relatório com os trades resultantes do replay (entrada,
  saída, motivo, PnL).
- **FR-005**: O sistema MUST comparar o resultado do replay contra um backtest simples do mesmo par/
  período, reportando o número de trades e retorno de cada lado.
- **FR-006**: Nenhuma tarefa desta spec MUST exigir dados privados, credenciais ou execução real em
  `TRADING_MODE=live` para ser validada — toda validação usa dados públicos.

### Key Entities

- **Sessão de replay**: execução isolada do motor de decisão real contra um histórico de candles,
  com seu próprio estado em memória (nunca persistido nos arquivos reais do bot).
- **Relatório de divergência**: comparação entre os trades do replay e os trades de um backtest
  simples do mesmo par/período.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Rodar `python main.py replay <PAR>` antes e depois não altera nenhum byte de
  `data/state.json`, `data/trades.csv`, `data/signals.csv` ou `data/decisions.csv` reais —
  verificável por hash/mtime antes e depois.
- **SC-002**: O replay produz um relatório legível comparando seus próprios trades contra um
  backtest do mesmo período, sem exigir que o operador rode os dois comandos separadamente e compare
  manualmente.
- **SC-003**: Todo o processo funciona com dados públicos da Binance — nenhuma credencial exigida.

## Assumptions

- "Motor de decisão real" reusa `handle_entry_candidate`/`handle_open_position` já existentes
  (`trading/position_lifecycle.py`) — não reimplementa essa lógica, evitando duas fontes de verdade
  sobre como o bot decide.
- Isolamento de arquivos reais é obtido substituindo temporariamente as funções de leitura/escrita
  (`load_state`/`save_state`/`log_trade`/`log_signal`/`log_decision`) usadas por `OrderManager` e
  pelos módulos de log por versões em memória, restauradas ao final do replay (mesmo padrão já usado
  extensivamente pela suíte de testes deste projeto para isolar `OrderManager` de disco real) — não
  um mecanismo novo, só aplicado fora do contexto de teste.
- MTF durante o replay busca dados públicos reais via a mesma função já usada em produção
  (`mtf_confirmed`) — não há risco de estado nisso, só leitura de mercado.
- Não modela latência de rede real nem falhas transitórias de execução (isso continua exigindo
  operação real, fora de escopo desta spec).
