"""Guarda contra o codigo e o registro de hipoteses desalinharem.

Motivacao: docs/research/registro-de-hipoteses.md S8 chama o proprio registro
de "o produto mais duravel da investigacao" -- um comando novo em main.py que
reivindica testar H<n> sem entrada correspondente no registro quebra
exatamente essa promessa, e nada mais no projeto detectaria isso sozinho.

Verifica so o sentido codigo -> doc (todo H<n> reivindicado como assunto
primario de um comando de main.py tem entrada no registro). O sentido
contrario nao vale: o registro tem hipoteses na fila (secao 6) que ainda nao
tem comando nenhum -- isso e esperado, nao drift.
"""

import re
from pathlib import Path

MAIN_PY = Path(__file__).resolve().parent.parent / "main.py"
REGISTRO = Path(__file__).resolve().parent.parent / "docs" / "research" / "registro-de-hipoteses.md"

# Mesmo padrao usado em toda docstring de comando que testa uma hipotese:
# '"""H8 -- arbitragem de funding rate...'.
PADRAO_COMANDO = re.compile(r'"""H(\d+)\s*--')

# As tres formas com que uma hipotese "estreia" no registro: cabecalho de
# secao 4 (H1-H21, testadas antes da reabertura), entrada em negrito da fila
# de secao 6 (H15+, incluindo bloqueadas), linha do quadro-resumo de 4.1.
PADROES_REGISTRO = (
    re.compile(r"^### 4\.\d+ H(\d+)\b", re.MULTILINE),
    re.compile(r"\*\*H(\d+)\s*[—-]"),
    re.compile(r"^\| H(\d+) \|", re.MULTILINE),
)


def _hipoteses_reivindicadas_no_codigo() -> set[str]:
    texto = MAIN_PY.read_text(encoding="utf-8")
    return set(PADRAO_COMANDO.findall(texto))


def _hipoteses_documentadas_no_registro() -> set[str]:
    texto = REGISTRO.read_text(encoding="utf-8")
    numeros: set[str] = set()
    for padrao in PADROES_REGISTRO:
        numeros.update(padrao.findall(texto))
    return numeros


def test_toda_hipotese_reivindicada_em_main_py_tem_entrada_no_registro():
    no_codigo = _hipoteses_reivindicadas_no_codigo()
    no_registro = _hipoteses_documentadas_no_registro()

    faltando = sorted((no_codigo - no_registro), key=int)
    assert not faltando, (
        f"main.py reivindica H{faltando} sem entrada correspondente em "
        f"docs/research/registro-de-hipoteses.md -- documente antes de mesclar "
        f"(ver S8 do proprio registro: e o produto mais duravel do projeto)."
    )


def test_o_padrao_de_extracao_encontra_pelo_menos_as_hipoteses_conhecidas():
    # Guarda contra os dois regex silenciosamente pararem de casar (ex.: um
    # reformato do markdown) e o teste acima passar so porque nao achou nada
    # dos dois lados.
    no_codigo = _hipoteses_reivindicadas_no_codigo()
    no_registro = _hipoteses_documentadas_no_registro()

    assert len(no_codigo) >= 15
    assert len(no_registro) >= 30
