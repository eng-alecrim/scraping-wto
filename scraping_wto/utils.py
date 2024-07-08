import os
import re
import unicodedata
from pathlib import Path
from random import randint
from time import sleep
from typing import Callable, Optional, Union

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())
NOME_PROJETO = os.getenv("NOME_PROJETO")
assert NOME_PROJETO is not None


def get_path_projeto(
    dir_atual: Path = Path.cwd(), nome_projeto: str = NOME_PROJETO
) -> Union[Callable, Path]:
    if dir_atual.name == nome_projeto:
        return dir_atual

    return get_path_projeto(dir_atual.parent, nome_projeto)


def normaliza_str(input_str: str) -> str:
    """
    Remove todos os caracteres especiais e acentos das letras, retornando uma string com apenas letras.

    Parameters:
    - input_str (str): Texto a ser tratado
    - minuscula (bool): Se é para deixar tudo minúsculo ou não

    Returns:
    - str: Texto tratado com apenas letras
    """
    # Importando as bibliotecas necessárias
    input_str = str(input_str)

    # Normalizando o texto conforme a forma NFC
    nfkd_form = unicodedata.normalize("NFKD", input_str)
    output_str = "".join([
        c for c in nfkd_form if not unicodedata.combining(c)
    ])

    # Removendo as possíveis tags de HTML
    regex_tags = r"</?.>"
    output_str = re.sub(regex_tags, "", output_str)

    # Substituindo os caracteres especiais e números (tudo o que NÃO estiver de A-z)
    regex = re.compile(r"[^a-zA-Z\s]+")

    tokens = regex.sub(" ", output_str).split()

    # Deixando em minúscula
    tokens = list(map(lambda x: x.lower(), tokens))

    # Removendo possíveis espaços em branco no início e/ou fim da string
    output_str = " ".join(map(lambda x: x.strip(), tokens)).strip()

    # Retorna algo apenas se o resultado NÃO for uma string vazia
    if output_str:
        return output_str
    return ""


def normaliza_nomes(input_str: Optional[str]) -> Optional[str]:
    if input_str is None:
        return None

    output_str = normaliza_str(input_str)
    output_str = output_str.replace(" ", "_")

    if output_str:
        return output_str

    return input_str


def tempo_espera_aleatorio() -> None:
    tempo_sleep = randint(75, 125) / 100
    sleep(tempo_sleep)

    return None
