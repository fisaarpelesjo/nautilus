# Feature Specification: H23 — prêmio de futuros trimestrais (contango) vs. funding perpétuo

**Feature Branch**: `059-h23-futuros-trimestrais`

**Created**: 2026-09-03

**Status**: Draft

**Input**: User description: H8 mede o carry de PERPÉTUOS (funding pago
a cada 8h, taxa variável, 23-47% dos pagamentos negativos medido).
Futuros com vencimento fixo (trimestrais, disponíveis na Binance)
convergem deterministicamente ao spot no vencimento — um mecanismo
estruturalmente diferente do funding: convergência garantida por
construção do contrato, não uma taxa periódica que o mercado decide.
Adicionada à fila em 2026-09-03 durante revisão de literatura junto com
H22/H24/H25/H26.

---

## Contexto e tese

**Por que um contrato diferente do de H8.** H8 revisou o carry de
funding perpétuo e mediu, sobre capital implantado (nocional + margem,
sem alavancagem), retorno bem abaixo do benchmark de 5% a.a. em todos
os pares testados. O mecanismo de H8 depende de uma taxa que pode
inverter de sinal a qualquer momento (23-47% dos pagamentos negativos).
Futuros com vencimento fixo eliminam essa variabilidade: o prêmio
(diferença entre o preço do futuro e o spot) é travado no momento da
entrada e converge deterministicamente ao vencimento — ganho ou perda
já conhecidos desde o início, sem depender de 1.095 pagamentos
periódicos incertos.

**Hipótese declarada antes de medir.** Sem verificação prévia de
magnitude — apenas a expectativa de que, sendo um mecanismo diferente
de H8, poderia ter economia diferente. Uma checagem rápida ao vivo
(fora desta spec, antes de escrever qualquer código) já indicou prêmio
bruto anualizado na faixa de 3-4,5% para os quatro contratos
disponíveis — mesma ordem de grandeza de H8, não necessariamente
melhor.

**Zero execução real.** Mede apenas — nenhuma ordem é enviada, nenhuma
permissão de API muda, nenhuma posição é aberta. Leitura de dado
público via `ccxt` (tickers de mercado futuro e spot).

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Medir o prêmio líquido sobre capital implantado por contrato (Priority: P1)

O pesquisador obtém, para cada contrato futuro trimestral disponível
(BTC/ETH, USDT-margined), o prêmio bruto anualizado, o líquido sobre
nocional (custo de H8 reusado) e o líquido sobre capital implantado —
comparado contra o mesmo benchmark de H8.

**Why this priority**: é a pergunta central da spec.

**Independent Test**: `avaliar_contrato` sobre um snapshot sintético de
preço futuro/spot produz os três números corretamente — sem rede.

**Acceptance Scenarios**:

1. **Given** um contrato futuro trimestral ativo, **When**
   `avaliar_contrato` roda, **Then** devolve prêmio bruto anualizado
   (pelos dias até o vencimento), líquido sobre nocional (custo de
   abertura+fechamento de H8) e líquido sobre capital implantado
   (metade do anterior).
2. **Given** o universo de contratos disponíveis, **When** listado,
   **Then** só inclui futuros com vencimento fixo (não perpétuos),
   cotados em USDT, para as bases pedidas.
3. **Given** um contrato com prêmio negativo (backwardation), **When**
   avaliado, **Then** calcula normalmente sem quebrar — não é tratado
   como erro.

---

### Edge Cases

- **Contrato de curto prazo** (poucos dias até o vencimento): o custo
  fixo de abertura+fechamento, anualizado sobre um prazo curto, pode
  superar o prêmio bruto e produzir retorno líquido NEGATIVO — resultado
  esperado e correto, não um bug.
- **Nenhum contrato disponível para a base pedida**: `avaliar_universo`
  devolve lista vazia, não erro nem zero silencioso.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST listar contratos futuros com vencimento
  fixo (não perpétuos) via `ccxt`, filtrados por base e quote.
- **FR-002**: O sistema MUST calcular o prêmio (`preço_futuro -
  preço_spot) / preço_spot`) e anualizá-lo pelos dias reais até o
  vencimento.
- **FR-003**: O sistema MUST reusar a mesma fórmula de custo
  (`CUSTO_ABERTURA_FECHAMENTO`) e benchmark (`BENCHMARK_RENDA_FIXA_AA`)
  de H8 (`backtesting/funding_carry.py`) — sem duplicar as constantes.
- **FR-004**: O sistema MUST calcular o retorno sobre capital
  implantado como metade do líquido sobre nocional (mesma lógica de
  H8: posição sem alavancagem exige nocional + margem = 2x capital).
- **FR-005**: O sistema MUST NOT enviar ordem real, alterar permissão
  de API nem modificar `trading/`, `execution/` ou `risk/`.

### Key Entities

- **ResultadoBasisContrato**: par, symbol, vencimento, dias até o
  vencimento, prêmio bruto a.a., líquido a.a. sobre nocional, líquido
  a.a. sobre capital implantado, se supera o benchmark.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `python main.py basis` produz uma tabela por contrato,
  ordenada por retorno sobre capital implantado.
- **SC-002**: O registro documenta quantos contratos (de quantos
  disponíveis) superam o benchmark sobre capital implantado.
- **SC-003**: Nenhuma ordem real é enviada; nenhuma permissão de API
  muda; produção permanece idêntica.

---

## Assumptions

- **Universo**: limitado pela realidade do mercado — só BTC/USDT e
  ETH/USDT têm contrato futuro trimestral USDT-margined na Binance
  (verificado 2026-09-03). Não é um universo escolhido, é o universo
  real disponível.
- **Retrato instantâneo, não série histórica**: diferente de H8 (funding
  rate tem histórico contínuo consultável), um contrato futuro vencido
  não tem preço consultável depois do vencimento — esta medição reflete
  o prêmio do dia da execução, para os contratos hoje listados.
  Limitação declarada, não escondida.
- Se o resultado for consistentemente abaixo do benchmark (esperado,
  dado a checagem preliminar), fecha mais uma frente sem justificar
  investimento em infraestrutura de futuros — mesma leitura de H8.
