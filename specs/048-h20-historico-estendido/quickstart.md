# Quickstart — validar a spec 048 (H20 com histórico estendido)

## Pré-requisitos

- Ambiente configurado (`pip install -r requirements.txt`).
- Acesso de rede à Binance (candles).
- Execução real: rodar na VPS (`vps-limulus`, `/root/nautilus-research`).

## 1. Rodar a suite (sem rede, mockada)

```bash
pytest tests/test_geometria.py -v
```

Confirma que o teto de candles mudou e que a regra de seleção continua
idêntica (constantes de spec 028 intocadas).

## 2. Rodar a avaliação real

```bash
python main.py geometria
```

Espera-se:

- Perfis das 6 geometrias candidatas sobre 6.000 candles.
- Geometria selecionada, razão pooled do subconjunto decidido, ponto
  de empate, e se supera o empate com banda de incerteza
  (`supera_empate`, Wilson CI).
- Comparação explícita contra os números de 2.000 candles já
  publicados (razão base 0,6223 em tp=2,0; razão pooled 0,7478;
  `supera_empate` = não).

## 3. Rodar a suite completa

```bash
pytest -q
```

## O que este quickstart não valida

Não decide se H20 (mesmo que revertida) reabriria uma frente de
melhoria para H14 além do que já foi medido nas specs 040-047 — isso
seria uma spec futura, condicionada ao resultado medido aqui.
