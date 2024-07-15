# =============================================================================
# BIBLIOTECAS E MÓDULOS
# =============================================================================

import logging
import logging.config
import os
import re
import unicodedata
import zipfile as zip
from pathlib import Path
from random import randint
from time import sleep
from typing import Callable, Optional, Union

from dotenv import find_dotenv, load_dotenv

# =============================================================================
# CONSTANTES
# =============================================================================

# -----------------------------------------------------------------------------
# Retorna o path da raiz do projeto
# -----------------------------------------------------------------------------

load_dotenv(find_dotenv())
NOME_PROJETO = os.getenv("NOME_PROJETO")
assert NOME_PROJETO is not None


def get_path_projeto(
    dir_atual: Path = Path.cwd(), nome_projeto: str = NOME_PROJETO
) -> Union[Callable, Path]:
    if dir_atual.name == nome_projeto:
        return dir_atual

    return get_path_projeto(dir_atual.parent, nome_projeto)


# -----------------------------------------------------------------------------
# Configurando o logger
# -----------------------------------------------------------------------------

DIR_PROJETO = get_path_projeto()
assert isinstance(DIR_PROJETO, Path)
DIR_LOG = DIR_PROJETO / "log"
DIR_LOG.mkdir(exist_ok=True, parents=True)

logging.config.fileConfig(DIR_PROJETO / "config/logging.toml")
LOGGER = logging.getLogger("logMain.info.debug")

# -----------------------------------------------------------------------------
# Número máximo de chars para um arquivo na WTO
# -----------------------------------------------------------------------------

NUMERO_MAX_CHARS_WTO = 15

# =============================================================================
# FUNÇÕES
# =============================================================================

# -----------------------------------------------------------------------------
# Verifica se um arquivo já foi extraído
# -----------------------------------------------------------------------------


def arquivo_ja_extraido(arquivo: Path, dir_destino: Path) -> bool:
    matches = list(dir_destino.glob(f"*{arquivo.name.split('_TL')[0]}*"))
    if matches:
        return True
    return False


# -----------------------------------------------------------------------------
# Extrai um arquivo zip
# -----------------------------------------------------------------------------


def extrai_arquivo(path_arquivo: Path, dir_destino: Optional[Path]) -> None:

    LOGGER.debug(f"extrai_arquivo: 📦 Extraindo '{path_arquivo.name}' . . .")
    zip_file = zip.ZipFile(file=path_arquivo, mode="r")
    zip_file.extractall(path=dir_destino if not None else path_arquivo.parent)
    LOGGER.debug(f"extrai_arquivo: ✅ '{path_arquivo.name}' foi extraído com sucesso!")

    return None


# -----------------------------------------------------------------------------
# Extrai todos os ZIP de um determinado diretório
# -----------------------------------------------------------------------------


def extraindo_todos_arquivos(dir_arquivos_zip: Path, dir_destino: Path) -> None:
    arquivos_zip = dir_arquivos_zip.glob(pattern="*.zip")

    LOGGER.debug("extraindo_todos_arquivos: 📦 EXTRAINDO ARQUIVOS ZIP")

    for arquivo_zip in arquivos_zip:
        if not arquivo_ja_extraido(arquivo_zip, dir_destino):
            extrai_arquivo(arquivo_zip, dir_destino)
        else:
            LOGGER.debug(
                f"extraindo_todos_arquivos: ✅ '{arquivo_zip.name}' já foi extraído!"
            )

    return None


# -----------------------------------------------------------------------------
# Normaliza uma string
# -----------------------------------------------------------------------------


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
    output_str = "".join([c for c in nfkd_form if not unicodedata.combining(c)])

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


# -----------------------------------------------------------------------------
# Normaliza o nome do país
# -----------------------------------------------------------------------------


def normaliza_nomes(input_str: str) -> str:

    output_str = normaliza_str(input_str[:NUMERO_MAX_CHARS_WTO])
    output_str = output_str.replace(" ", "_")

    if output_str:
        assert (
            len(output_str) <= NUMERO_MAX_CHARS_WTO
        ), f"normaliza_nomes: ERRO! Nome normalizado com >{NUMERO_MAX_CHARS_WTO} chars."
        return output_str

    return input_str[:NUMERO_MAX_CHARS_WTO].lower().replace(" ", "_")


# -----------------------------------------------------------------------------
# Faz o código dormir por um tempo aleatório (default: entre .75~1.25s)
# -----------------------------------------------------------------------------


def tempo_espera_aleatorio(min: int = 75, max: int = 125) -> None:

    tempo_sleep = randint(min, max) / 100
    sleep(tempo_sleep)

    return None


# -----------------------------------------------------------------------------
# Extraí o nome de um país a partir de uma string <- APENAS ARQ DOWNLOADS
# -----------------------------------------------------------------------------


def extrai_nome_pais(texto: str) -> str:

    regex = r".*/(.*)_TL.*"

    if re.findall(regex, texto):
        return re.findall(regex, texto)[0]
    return ""
