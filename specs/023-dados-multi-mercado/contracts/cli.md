# Contrato: Interface de linha de comando

**Feature**: 023-dados-multi-mercado

---

## Princípio

Nenhum comando existente muda de assinatura. Símbolos de mercados novos são aceitos **onde símbolos já eram aceitos** — o operador não precisa aprender sintaxe nova nem informar o mercado, que é deduzido do formato do símbolo.

---

## Comandos existentes — comportamento estendido

| Comando | Antes | Depois |
|---|---|---|
| `python main.py backtest [SÍMBOLO]` | só cripto | aceita qualquer símbolo resolvível |
| `python main.py edge [SÍMBOLO]` | só cripto | idem |
| `python main.py compare` | pares cripto fixos | aceita lista multi-mercado |
| `python main.py scan` | top pares Binance por volume | **inalterado** — é cripto por natureza (usa `fetch_tickers`) |
| `python main.py optimize` | pares cripto | aceita símbolos multi-mercado |
| `python main.py bot` | opera cripto | **inalterado**, e agora recusa símbolo não-cripto na inicialização (FR-007) |

Exemplos de símbolo aceitos: `BTC/USDT` (cripto), `AAPL` (ação EUA), `PETR4.SA` (ação BR), `EURUSD=X` (forex), `ES=F` (futuro), `^GSPC` (índice).

---

## Comando novo: varredura multi-mercado

```
python main.py multimarket
```

Varre combinações de estratégia × símbolo e aplica a confirmação obrigatória fora da janela de busca (FR-012/013/014).

### Saída obrigatória

1. **Contagem de combinações avaliadas**, em destaque — para que uma aprovação isolada seja lida com o peso estatístico correto (FR-013)
2. **Tabela ranqueada** com, por linha: estratégia, símbolo, mercado, métricas da janela de busca, métricas da janela de confirmação e status
3. **Status visualmente distinto** entre:
   - `confirmado` — passou na janela de confirmação
   - `so na busca` — passou apenas onde foi descoberto; **MUST NOT** ser apresentado como aprovado (FR-014)
   - `reprovado`
   - `inconclusivo` — histórico insuficiente para dividir as janelas
4. **Mercado e perfil de custo** aplicados a cada linha (FR-011)
5. **Aviso de gap** nas linhas de mercado descontínuo (FR-009)

### Regras de comportamento

- Um símbolo que falhe ao buscar dados MUST aparecer marcado como erro, sem interromper os demais (US3, cenário 2)
- Um mercado sem perfil de custo declarado MUST ser recusado com motivo explícito, nunca avaliado com custo de outro mercado (FR-004)
- O relatório MUST ser exportado por `utils/report_export.py`, como os demais comandos de pesquisa — sem pipeline paralelo (Princípio V da Constituição)

---

## Contrato de configuração

`config/settings.py` MUST:

- Aceitar símbolos não-cripto na lista usada por comandos de **pesquisa**
- Manter a validação de formato `/USDT` para a lista usada pela **operação** — relaxar essa validação globalmente reabriria o caminho para um símbolo inoperável chegar ao loop ao vivo, que é exatamente o que FR-007 impede
- Expor os perfis de custo por mercado de forma auditável e sobrescrevível por `.env`
