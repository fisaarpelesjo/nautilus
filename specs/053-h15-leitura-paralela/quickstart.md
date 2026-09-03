# Quickstart — validar a spec 053 (H15 leitura paralela)

## Pré-requisitos

- Ambiente configurado (`pip install -r requirements.txt`).
- Acesso de rede às seis corretoras públicas (opcional para os testes,
  que simulam latência sem rede real).
- Nova campanha real: rodar na VPS (`vps-limulus`,
  `/root/nautilus-research`).

## 1. Rodar a suite (sem rede, latência simulada)

```bash
pytest tests/test_arbitragem.py -v
```

Cobre: tempo total de `medir_ciclo` fica próximo de UMA leitura, não
de seis somadas (paralelismo real, medido via `time.sleep` simulado);
falha isolada de uma corretora continua não abortando o ciclo.

## 2. Rodar um ciclo real

```bash
python main.py arbitragem BTC/USDT
```

Espera-se: `intervalo_ms` bem menor entre a maioria das combinações —
não mais dominado pela ordem fixa de leitura.

## 3. Rodar a suite completa

```bash
pytest -q
```

## O que este quickstart não valida

Não decide o veredito de H15 — só corrige o instrumento para que a
campanha real (a rodar de novo depois, spec futura) meça as 14
combinações que nunca puderam ser medidas até aqui.
