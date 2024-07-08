from time import time

import pytest

from scraping_wto.utils import (
    get_path_projeto,
    normaliza_nomes,
    tempo_espera_aleatorio,
)

NOME_PROJETO = "scraping-wto"
TEMPO_MINIMO_SLEEP = 0.75


def test_get_path_projeto() -> None:
    # path_teste = Path(f"{NOME_PROJETO}/dir1/dir2")
    assert get_path_projeto().name == NOME_PROJETO
    return None


@pytest.mark.parametrize(
    (
        "string",
        "esperado",
    ),  # nome dos argumentos do testeame of our test's arguments
    [
        (None, None),  # casos para testar
        ("", ""),
        ("Olá!", "ola"),
        ("Eu recebo R$ 1.000,00 por mês!", "eu_recebo_r_por_mes"),
    ],
)
def test_normaliza_nomes(string: str, esperado: str) -> None:
    resultado = normaliza_nomes(string)
    assert resultado == esperado
    return None


def test_tempo_espera_aleatorio() -> None:
    t_inicio = time()
    return_funcao = tempo_espera_aleatorio()
    tempo_duracao = time() - t_inicio

    assert return_funcao is None
    assert tempo_duracao >= TEMPO_MINIMO_SLEEP

    return None
