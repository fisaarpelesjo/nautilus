# Fase 1 — Modelo de dados: H17

Nenhuma entidade nova além do que H14 (`AvaliacaoH14`, `ResultadoModelo`,
`ParametrosBarreira`) e spec 033 (`fetch_onchain_series`) já definem. Esta
fase é sobre como eles se conectam.

## `avaliar_par()` — parâmetros novos (`backtesting/modelo.py`)

| Parâmetro | Tipo | Default | Efeito |
|---|---|---|---|
| `atributos` | `list[str]` | `ATRIBUTOS` (constante módulo) | Colunas usadas por `estimar`/`prever` — hoje as 5 de H14 |
| `extrair_atributos_fn` | `Callable[[pd.DataFrame], pd.DataFrame]` | `extrair_atributos` (função módulo) | Como as colunas são calculadas a partir do candle preparado |

**Invariante (D4, testado):** `avaliar_par(par)` sem os dois parâmetros
novos produz `AvaliacaoH14` idêntico ao código antes desta spec, para o
mesmo par e mesmo `df`.

## `construir_extrator_onchain(serie_growth)` (`backtesting/onchain_hipotese.py`, novo)

Fábrica que fecha sobre a série de crescimento on-chain já calculada e
devolve uma função compatível com `extrair_atributos_fn`:

```python
def construir_extrator_onchain(serie_growth: pd.Series) -> Callable[[pd.DataFrame], pd.DataFrame]:
    def extrator(prep: pd.DataFrame) -> pd.DataFrame:
        x = extrair_atributos(prep)          # os 5 de H14, reusados
        x["onchain_addr_growth_7d"] = _merge_causal(prep.index, serie_growth)
        return x
    return extrator
```

| Função | Entrada | Saída |
|---|---|---|
| `onchain_addr_growth_7d(serie_enderecos)` | `pd.Series` diária de `n-unique-addresses` | `pd.Series` diária: `(ma7 - ma7.shift(7)) / ma7.shift(7)` |
| `_merge_causal(indice_candles, serie_diaria)` | índice de candles + série diária | `pd.Series` alinhada aos candles: valor do dia `D-1` completo para cada candle no dia `D` (D5) |

## Estados de `AvaliacaoH14` (reusados, sem mudança)

Mesma tabela já definida em `specs/027-aprendizado-barreira-tripla/
data-model.md` — `erro`, `nao_convergiu`, `classe_unica`, `inconclusivo`
(×2), `sem_sinal`, `insuficiente`, `piora`, `sem_vantagem`, `confundido`,
`so_na_busca`, `melhora`. H17 não adiciona estado novo — a comparação
isolada (5 vs 5+on-chain) usa dois objetos `AvaliacaoH14`, cada um
classificado pela régua já existente.

## `RelatorioH17` (novo, `backtesting/onchain_hipotese.py`)

| Campo | Descrição |
|---|---|
| `avaliacao_base` | `AvaliacaoH14` com os 5 atributos originais, BTC/USDT |
| `avaliacao_onchain` | `AvaliacaoH14` com os 5 + `onchain_addr_growth_7d`, mesmo par/período |
| `correlacao_onchain` | `dict[str, float]` — colinearidade medida (D2), exibida no relatório |
| `atributo_declarado` | `"onchain_addr_growth_7d"`, string fixa — nunca varia entre execuções |

A comparação central (SC-001) é `avaliacao_onchain.razao_chances_decidido`
contra `avaliacao_base.razao_chances_decidido` — mesmos eventos, mesma
janela de teste (`div` idêntico entre as duas chamadas de `avaliar_par`,
já que usam o mesmo `df`/purga).
