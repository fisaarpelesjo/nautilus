# Research: H29 — pairs trading via cópula gaussiana

## D1 — precondição de cointegração verificada com dado real antes de qualquer código

Antes de escrever `backtesting/pairs_copula.py`, `selecionar_pares`/
`PairsParams(formacao=500)` de H10 (sem alteração nenhuma) rodaram
sobre `UNIVERSO_AMPLO_HISTORICO_COMPLETO` (22 pares, 6.000 candles,
dado real via `fetch_ohlcv`):

```
candles comuns: 6000
pares cointegrados encontrados (janela final): 3
  SOL/USDT-AVAX/USDT meia_vida=9.6  adf_p=0.0003
  ETH/USDT-AVAX/USDT meia_vida=13.5 adf_p=0.0066
  BNB/USDT-AVAX/USDT meia_vida=15.7 adf_p=0.0174
```

**A precondição está satisfeita.** Existem pares genuinamente
cointegrados (meia-vida curta, ADF significativo) neste universo hoje
— H10 foi reprovada pelo SINAL de entrada/saída sobre esses pares
(z-score, PF 0,15), não pela ausência de uma relação real para
explorar. Construir a cópula sobre um universo sem cointegração real
teria sido desperdício de esforço numa pergunta já respondida por H10;
não é o caso aqui.

## D2 — método: cópula gaussiana, abordagem "return-based" (Tadi & Witzany 2025)

`docs/research/copula-based-trading-of-cointegrated-cryptocurrency-pairs.md`
(já citado nas referências do registro) descreve dois métodos: um
baseado em retorno (per-período) e um "level-based" que acumula o
desvio de 0,5 ao longo de múltiplos períodos (CMI, mispricing index
cumulativo, Xie & Wu 2013). **Declarado antes de medir: usar o método
return-based, mais simples** — mesma disciplina de simplicidade que já
funcionou em H14 ("6 parâmetros bastaram, a capacidade do modelo não
era o gargalo"). Não testar as duas abordagens e escolher a que
performar melhor — isso repetiria exatamente o erro que a comparação
contra embaralhado (H14) e a disciplina de pré-registro (H5/H25)
existem para evitar.

**Fórmula (Eq. 4 do paper):**

```
h(u1|u2) = P(U1 <= u1 | U2 = u2) = ∂C(u1,u2)/∂u2
```

Para a cópula gaussiana bivariada, forma fechada:

```
h(u1|u2) = Φ((Φ⁻¹(u1) - ρ·Φ⁻¹(u2)) / √(1-ρ²))
```

`ρ` é a correlação de Pearson sobre os ESCORES NORMAIS das marginais
transformadas via CDF empírica (Sklar) — não sobre os retornos brutos,
que podem ter caudas pesadas que distorceriam Pearson diretamente.

## D3 — corte de entrada/saída, declarado antes de medir

- **Entrada**: `h1|2 <= 0,05` — o retorno de `a` está no percentil 5%
  inferior ou abaixo, condicionado ao retorno de `b` — `a` ficou
  anormalmente barato em relação a `b`. Mesma lógica direcional de H10
  (compra o ativo que ficou barato), instrumento estatístico diferente.
- **Saída**: `h1|2 >= 0,5` — retorno à condição de equilíbrio (nenhum
  desvio condicional).
- **Stop**: `h1|2 <= 0,01` — divergência mais extrema ainda depois de
  já ter entrado, abandona a tese. Mais apertado que o corte de entrada
  (0,05) de propósito — o stop não deveria disparar na MESMA magnitude
  que já justificou a entrada, só numa divergência adicional.

Esses três números são análogos em espírito aos `entrada_z`/`saida_z`/
`stop_z` de H10, só que no espaço de probabilidade condicional (0 a 1)
em vez de desvios-padrão.

## D4 — universo e split

`UNIVERSO_AMPLO_HISTORICO_COMPLETO` (22 pares, mesmo de H10) — mesmo
`split_treino_validacao`, mesma cadência de reseleção corrigida por
spec 054 (120 candles, `meia_vida_max`, não os 500 originais que
famintaram a amostra) — reusar a correção já estabelecida, não
reintroduzir o bug já corrigido.

## D5 — benchmark de comparação

Números já publicados de H10 (spec 054, o resultado final e correto):
validação 10 trades, profit factor 0,15, drawdown 16,61%. Qualquer
leitura desta spec é lida ao lado desses números, nunca os substituindo.

## Hipótese declarada antes da medição final

**Principal:** a cópula produz resultado materialmente diferente
(melhor) de H10.

**Alternativa, com igual peso:** o sinal muda, o resultado econômico
não — consistente com a leitura acumulada do registro (§8) de que o
obstáculo é custo/geometria de saída, não a forma exata do sinal
estatístico.

## Reprodução

`python main.py pairs_copula` · `reports/pairs_copula_*.json`.

(Resultado real preenchido após a execução — ver
`docs/research/registro-de-hipoteses.md` §6.1 para o número medido.)
