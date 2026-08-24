# Feature Specification: Camada de dados multi-mercado para pesquisa

**Feature Branch**: `023-dados-multi-mercado`

**Created**: 2026-08-24

**Status**: Draft

**Input**: User description: "Camada de dados multi-mercado para pesquisa (somente leitura, sem execução). Permitir que o motor de backtest já existente avalie estratégias em mercados NÃO-cripto — ações, forex, futuros, índices — sem construir execução real para esses mercados."

## Contexto

O bot enxerga apenas cripto (Binance via ccxt). Oito dias de medição estabeleceram que a estratégia atual não tem vantagem preditiva nesse mercado: profit factor mediano `0,60` no scan de 30 pares, paper mode em `-$18,27` após 17 trades, e uma grade de 648 combinações de parâmetros cujo melhor retorno médio foi `+0,23%` em ~333 dias.

A pergunta que o operador precisa responder — *"alguma combinação de estratégia × mercado tem vantagem real?"* — é hoje **impossível de responder**, porque não há como apontar o motor de backtest para nada além de cripto.

Esta feature entrega **capacidade de medição, não de operação**. O objetivo é descobrir onde vale investir esforço **antes** de construir corretora e execução para qualquer mercado novo.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Avaliar uma estratégia em mercado não-cripto (Priority: P1)

O operador quer saber se a estratégia atual se comporta melhor em ações, forex ou futuros do que em cripto. Ele informa um símbolo desses mercados a um comando de pesquisa e recebe as mesmas métricas que já usa para cripto — retorno, profit factor, drawdown, win rate, veredito de aprovação — calculadas pelo mesmo motor.

**Why this priority**: É a capacidade inteira em uma frase. Sem ela, nenhuma das outras histórias tem propósito, e a pergunta que motiva a feature continua sem resposta.

**Independent Test**: Rodar um backtest sobre um símbolo de ações e obter um relatório completo, comparável lado a lado com o de um par cripto. Entrega valor sozinha: já permite a primeira resposta sobre se vale a pena olhar o mercado.

**Acceptance Scenarios**:

1. **Given** um símbolo de ações válido, **When** o operador roda um backtest sobre ele, **Then** recebe o mesmo conjunto de métricas e veredito que receberia para um par cripto
2. **Given** um símbolo cripto, **When** o operador roda qualquer comando de pesquisa, **Then** o resultado é idêntico ao que era antes desta feature (nenhuma regressão)
3. **Given** um símbolo inexistente ou sem histórico suficiente, **When** o operador tenta avaliá-lo, **Then** recebe uma mensagem explícita de dado indisponível — nunca um resultado numérico que pareça válido

---

### User Story 2 - Custo de execução condizente com o mercado avaliado (Priority: P1)

Ao avaliar um mercado novo, o operador precisa que taxa e slippage usados na simulação sejam os daquele mercado, não os de cripto. Corretagem de ações, spread de forex e custo por contrato de futuros são estruturalmente diferentes de uma taxa percentual de exchange cripto.

**Why this priority**: Empatada em P1 com a História 1 porque **um resultado com o custo errado é pior que nenhum resultado** — ele parece confiável e leva a decisão errada. Este projeto já foi mordido exatamente por isso: pares de book fino (ACE, BIO, ALLO) pareceram operáveis no backtest porque o slippage simulado era o de um par ultra-líquido, e entregaram prejuízo real. Entregar a História 1 sem esta seria reproduzir o mesmo erro em escala maior.

**Independent Test**: Rodar o mesmo símbolo com perfis de custo diferentes e verificar que as métricas mudam de forma coerente com o custo aplicado; e que um símbolo de mercado novo nunca é avaliado com o custo padrão de cripto por omissão.

**Acceptance Scenarios**:

1. **Given** um símbolo de um mercado com custo configurado, **When** ele é avaliado, **Then** a simulação aplica o custo daquele mercado
2. **Given** um símbolo de um mercado **sem** custo configurado, **When** ele é avaliado, **Then** o sistema recusa ou sinaliza explicitamente a lacuna — MUST NOT cair silenciosamente no custo de cripto
3. **Given** dois mercados com custos diferentes, **When** o mesmo comportamento de preço é simulado em ambos, **Then** o de custo maior apresenta resultado líquido pior

---

### User Story 3 - Comparar estratégias e mercados numa execução (Priority: P2)

O operador quer varrer combinações — várias estratégias contra vários símbolos de mercados diferentes — e ver o resultado ranqueado numa única saída, como já faz hoje com pares cripto.

**Why this priority**: Multiplica o valor das histórias P1, mas não é pré-requisito delas. Um operador pode responder a pergunta central rodando um símbolo por vez; isso apenas torna a varredura prática.

**Independent Test**: Rodar uma comparação com símbolos de pelo menos dois mercados distintos e obter uma tabela única, ordenada pelo mesmo critério de qualidade já usado hoje.

**Acceptance Scenarios**:

1. **Given** uma lista de símbolos de mercados diferentes, **When** o operador roda uma comparação, **Then** recebe uma tabela única com todos, ranqueada pelo critério existente
2. **Given** um símbolo da lista falha ao buscar dados, **When** a comparação roda, **Then** os demais são avaliados normalmente e o que falhou aparece marcado como erro

---

### User Story 4 - Preservação integral do bot ao vivo (Priority: P1)

O operador tem um bot rodando 24/7 em paper mode acumulando histórico real. Nada nesta feature pode alterar esse comportamento — nem o que ele opera, nem como decide, nem os custos que simula.

**Why this priority**: P1 por ser uma restrição de segurança, não uma funcionalidade. O histórico em acumulação é o ativo mais valioso do projeto neste momento, e a Constituição (Princípio I) exige que mudanças no caminho de execução passem por validação em paper mode antes de valerem.

**Independent Test**: Comparar o comportamento do loop ao vivo antes e depois da mudança sobre a mesma configuração cripto — decisões, custos e ordem de checagens devem ser idênticos.

**Acceptance Scenarios**:

1. **Given** a configuração cripto atual, **When** o bot roda seu ciclo de decisão, **Then** o comportamento é idêntico ao anterior a esta feature
2. **Given** um símbolo não-cripto configurado por engano no caminho de operação, **When** o bot inicia, **Then** ele recusa de forma explícita — MUST NOT tentar operar um mercado sem execução implementada

---

### Edge Cases

- **Símbolo sem histórico suficiente** para o aquecimento dos indicadores: deve ser reportado como inconclusivo, não avaliado com amostra insuficiente
- **Mercado com pregão fechado / feriado**: lacunas na série não podem ser interpretadas como movimento de preço
- **Gap de abertura** (mercados que não operam 24h): a série tem descontinuidade entre fechamento e abertura seguinte — o resultado precisa deixar claro que a proteção de perda por trade não age dentro de um gap
- **Símbolo que existe em mais de um mercado** (mesmo ticker em bolsas diferentes): a resolução deve ser inequívoca
- **Fonte de dados indisponível ou com falha de rede**: falha fechada, sem resultado parcial que pareça completo
- **Restrição estrutural do mercado** que impeça operar o símbolo (lote mínimo, papel suspenso, contrato vencido): equivalente ao que já existe para preço mínimo em cripto — precisa aparecer na avaliação, não só no caminho de operação

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST permitir avaliar estratégias sobre símbolos de mercados além de cripto, usando o mesmo motor de simulação, as mesmas métricas e o mesmo critério de veredito já aplicados hoje
- **FR-002**: O sistema MUST manter cripto como o mercado padrão, com comportamento inalterado quando nenhum mercado é especificado
- **FR-003**: O sistema MUST associar a cada mercado um perfil de custo próprio (taxa e slippage) e aplicá-lo na simulação daquele mercado
- **FR-004**: O sistema MUST recusar ou sinalizar explicitamente a avaliação de um símbolo cujo mercado não tenha perfil de custo definido — MUST NOT usar o custo de outro mercado por omissão
- **FR-005**: O sistema MUST tratar indisponibilidade de dado (rede, símbolo inexistente, histórico insuficiente) como falha explícita, nunca como resultado válido ou valor zero
- **FR-006**: O sistema MUST preservar integralmente o comportamento do caminho de operação ao vivo para cripto — decisões, custos e sequência de verificações idênticos aos anteriores
- **FR-007**: O sistema MUST impedir que o caminho de operação ao vivo aceite um símbolo de mercado sem execução implementada, recusando de forma explícita na inicialização
- **FR-008**: O sistema MUST aceitar, na configuração, identificadores de símbolo de mercados não-cripto, sem afastar a validação que hoje protege a configuração de operação cripto
- **FR-009**: O sistema MUST sinalizar, no resultado de um mercado com pregão descontínuo, que a proteção de perda por trade não age dentro de um gap de abertura
- **FR-010**: O sistema MUST permitir comparar, numa única execução, símbolos de mercados diferentes, apresentando-os sob o mesmo critério de ranqueamento
- **FR-011**: O sistema MUST registrar, junto de cada resultado de pesquisa, qual mercado e qual perfil de custo foram usados, de modo que o número seja auditável depois
- **FR-012**: Numa varredura de múltiplas combinações de estratégia × símbolo, o sistema MUST NOT declarar uma combinação aprovada com base apenas na janela usada para descobri-la — a aprovação MUST exigir confirmação numa janela de dados separada, que não participou da busca
- **FR-013**: O sistema MUST registrar, no resultado de uma varredura, quantas combinações foram avaliadas — de modo que o operador possa julgar o peso estatístico de uma aprovação isolada
- **FR-014**: O sistema MUST distinguir, no resultado, uma combinação que passou apenas na janela de busca de uma que passou também na janela de confirmação — a primeira MUST NOT ser apresentada como aprovada

### Key Entities

- **Mercado**: categoria de ativos com características próprias de negociação — continuidade (24/7 ou pregão), perfil de custo, convenção de identificação de símbolo. Exemplos: cripto, ações, forex, futuros, índices
- **Fonte de dados**: origem de séries históricas de preço para um ou mais mercados. Um mercado é atendido por exatamente uma fonte por vez; uma fonte pode atender vários mercados
- **Perfil de custo**: taxa e slippage aplicáveis a um mercado, usados pela simulação para calcular o resultado líquido
- **Símbolo**: identificador de um ativo negociável dentro de um mercado, resolvido de forma inequívoca para uma fonte de dados

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: O operador consegue obter métricas completas de uma estratégia sobre um símbolo não-cripto sem escrever código — apenas informando o símbolo a um comando existente
- **SC-002**: Métricas de mercados diferentes aparecem lado a lado, sob o mesmo critério de aprovação, numa única saída
- **SC-003**: Nenhum resultado de pesquisa é produzido com custo de mercado incorreto: 100% dos resultados registram qual perfil de custo foi aplicado
- **SC-004**: O comportamento do bot em operação cripto permanece idêntico — verificável comparando as decisões do ciclo antes e depois da mudança sobre a mesma configuração
- **SC-005**: Toda falha de dado resulta em mensagem explícita: zero resultados numéricos produzidos a partir de dado ausente ou incompleto
- **SC-006**: O operador consegue responder, com evidência medida, se alguma combinação de estratégia e mercado supera o critério de aprovação já usado no projeto
- **SC-007**: Nenhuma combinação é apresentada como aprovada sem ter passado numa janela de dados que não participou da sua descoberta — 100% das aprovações são confirmadas fora da amostra de busca

## Assumptions

- **Fonte de dados sem custo**: assume-se uma fonte pública e gratuita, sem necessidade de chave paga, cobrindo ações, forex, futuros e índices. A qualidade de dado gratuito é inferior à de fornecedor pago (ajustes de proventos, precisão intradiária) — aceitável porque o objetivo é triagem, não decisão final de operação
- **Granularidade**: assume-se que a fonte oferece a mesma granularidade de tempo já usada em cripto para os mercados avaliados. Onde não oferecer, o mercado é avaliado na granularidade disponível e isso é registrado no resultado
- **Custo fixo por ordem**: mercados que cobram corretagem fixa (não percentual) serão representados por um percentual equivalente ao tamanho de ordem configurado. É uma aproximação — precisa e suficiente para triagem, imprecisa para dimensionamento fino
- **Sem execução**: nenhuma ordem — real ou simulada em paper mode — será enviada para mercado não-cripto. A Constituição restringe operação a Binance Spot, e esta feature não altera isso
- **Sem estratégias novas**: esta feature habilita medição de estratégias existentes em mercados novos; criar estratégia adequada a cada mercado é trabalho posterior e separado
- **Gaps não são modelados no caminho de operação**: tratar gap de abertura na proteção de perda é problema do dia em que houver execução para esses mercados — aqui apenas se sinaliza a limitação no resultado
- **Reuso obrigatório**: o motor de simulação, o critério de aprovação e a exportação de relatórios existentes são reutilizados sem duplicação, conforme o histórico do projeto de evitar caminhos paralelos que divergem silenciosamente

## Dependências

- Motor de simulação, validação out-of-sample, comparação e critério de aprovação existentes (`backtesting/`)
- Configuração central de parâmetros e sua validação (`config/`)
- Suíte de testes existente (`tests/`) — conforme Princípio III da Constituição, estendida e não substituída

## Riscos

- **Descoberta por acaso**: avaliar muitas combinações aumenta a chance de encontrar vantagem inexistente — com o profit factor mediano observado, é matematicamente esperado que algumas passem por sorte. Mitigado por FR-012/FR-014 (confirmação obrigatória fora da janela de busca), reusando a infraestrutura de validação out-of-sample que o projeto já possui. Este projeto já reconheceu o risco correlato de viés de seleção ao recusar recortar a lista de pares pelos melhores resultados do mesmo histórico
- **Encurtamento da janela de teste**: exigir confirmação fora da amostra divide o histórico disponível entre busca e confirmação, reduzindo a amostra de cada uma. É o custo aceito da decisão acima — uma aprovação sobre histórico dividido vale mais que uma aprovação sobre o histórico inteiro que a descobriu
- **Falsa sensação de progresso**: a feature entrega capacidade de medir, não vantagem competitiva. Se todos os mercados reprovarem, o resultado é legítimo e valioso — encerra a linha de investigação com evidência em vez de intuição
- **Divergência entre caminhos**: introduzir uma segunda fonte de dados cria a possibilidade de os caminhos de pesquisa e de operação discordarem. O projeto já foi atingido duas vezes por esse padrão (simulação sem trailing stop; confirmação de tendência olhando o futuro), e ambas as vezes o defeito passou despercebido por não haver teste comparando os dois caminhos
