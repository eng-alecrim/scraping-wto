from pathlib import Path
from typing import Callable, Union


def get_path_projeto(dir_atual: Path = Path.cwd()) -> Union[Callable, Path]:
    from dotenv import load_dotenv, find_dotenv
    import os

    load_dotenv(find_dotenv())
    nome_projeto = os.getenv("NOME_PROJETO")

    if dir_atual.name == nome_projeto:
        return dir_atual

    return get_path_projeto(dir_atual.parent)


def normaliza_nomes(input_str: str) -> str:
    import unicodedata
    import re

    nfkd_form = unicodedata.normalize("NFKD", input_str)
    output_str = "".join([c for c in nfkd_form if not unicodedata.combining(c)])

    regex = re.compile(r"[^a-zA-Z\s]+")
    output_str = regex.sub("", output_str).lower()

    output_str = output_str.strip().replace(" ", "_")

    if output_str != "":
        return output_str

    return input_str


def tempo_espera_aleatorio() -> None:
    from random import randint
    from time import sleep

    tempo_sleep = randint(75, 125) / 100
    sleep(tempo_sleep)

    return None
