# Documentação — Nautilus

Documentação completa do bot, organizada por capítulos. Cada capítulo é independente — pode ler na ordem ou pular direto pro tópico que precisa.

## Sumário

| # | Capítulo | Conteúdo |
|---|---|---|
| 01 | [Visão Geral](01-visao-geral.md) | O que é o projeto, filosofia, arquitetura, estrutura de diretórios |
| 02 | [Instalação](02-instalacao.md) | Pré-requisitos, setup do ambiente, primeira execução |
| 03 | [Estratégia](03-estrategia.md) | Indicadores, regras de entrada/saída, filtros opcionais |
| 04 | [Gestão de Risco](04-gestao-risco.md) | Stop loss, take profit, trailing stop, drawdown, position sizing |
| 05 | [Execução de Ordens](05-execucao-ordens.md) | Paper vs live, custos simulados, ordens limit, liquidez |
| 06 | [Proteções Operacionais](06-protecoes-operacionais.md) | Circuit breaker, kill switch, reconciliação |
| 07 | [Configuração](07-configuracao.md) | Referência completa de todas as variáveis do `.env` |
| 08 | [Comandos CLI](08-comandos-cli.md) | Todos os comandos `python main.py` |
| 09 | [Persistência de Dados](09-persistencia-dados.md) | Arquivos gerados, formatos, o que cada um contém |
| 10 | [Observabilidade](10-observabilidade.md) | Painel, debug, performance, replay — como investigar o bot |
| 11 | [Deploy em Produção](11-deploy-producao.md) | Rodar 24/7 num servidor (guia genérico) |
| 12 | [Desenvolvimento](12-desenvolvimento.md) | Fluxo de contribuição, testes, como adicionar uma estratégia |
| 13 | [Metodologia SDD](13-metodologia-sdd.md) | Como o projeto é desenvolvido (spec-driven development) |
| 14 | [Multi-mercado](14-multi-mercado.md) | Avaliar estratégias em ações, forex e futuros (pesquisa, não operação) |

## Convenções usadas nesta documentação

- Todo valor de configuração mostrado (`VARIAVEL=valor`) foi conferido contra `config/settings.py` no momento da escrita — não contra suposição.
- Diagramas usam [Mermaid](https://mermaid.js.org/), renderizado nativamente pelo GitHub.
- `→` indica fluxo/sequência; `⇢` indica dependência opcional (filtro desligado por padrão).
- Caminhos de arquivo são relativos à raiz do repositório.

Voltar para o [README principal](../README.md).
