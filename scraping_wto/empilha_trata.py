# =============================================================================
# BIBLIOTECAS E MÓDULOS
# =============================================================================

import re
import unicodedata
from collections import Counter
from functools import reduce
from pathlib import Path
from time import time
from typing import List, Optional

from scraping_wto.schemas import TipoRelatorio
from scraping_wto.utils import get_path_projeto

# =============================================================================
# CONSTANTES
# =============================================================================

DIR_PROJETO = get_path_projeto()
assert isinstance(DIR_PROJETO, Path)
DIR_DADOS = DIR_PROJETO / "data/bronze/tl"
DIR_DESTINO = DIR_DADOS / "empilhado"
DIR_DESTINO.mkdir(exist_ok=True, parents=True)

RELATORIOS = [
    TipoRelatorio(nome="Duty Details", regex="*DutyDetails*.txt"),
    TipoRelatorio(nome="PTA Trade Details", regex="*PTATradeDetails*.txt"),
    TipoRelatorio(nome="Tariff Details", regex="*TariffDetails*.txt"),
    TipoRelatorio(nome="Trade Details", regex="*TradeDetails*.txt"),
]

# =============================================================================
# FUNÇÕES
# =============================================================================


# -----------------------------------------------------------------------------
# Função resposntável por fazer o empilhamento
# -----------------------------------------------------------------------------


def f_reduce(empilhado: Optional[str], path_arquivo: str) -> str:
    with open(path_arquivo, "r", encoding="utf-8") as csv_f:
        linhas: list[str] = csv_f.readlines()
    if empilhado is None:
        linha_cols: str = linhas[0].replace("\n", "")
        cols_renomeadas: List[str] = rename_duplicates(
            list(
                map(
                    lambda nome_col: normaliza_nome_coluna(nome_col),
                    linha_cols.split("\t"),
                )
            )
        )
        linhas[0] = "\t".join(cols_renomeadas) + "\n"
        return "".join(linhas)
    csv = "".join(linhas[1:])

    return empilhado + csv


# -----------------------------------------------------------------------------
# Função resposntável por normalizar o nome da coluna para o nosso padrão
# -----------------------------------------------------------------------------


def normaliza_nome_coluna(input_str: str) -> str:
    """
    Função que remove todos os caracteres especiais e acentos das letras, retornando uma str com apenas letras.
    :param input_str:
    :param minuscula:
    """

    # Garantindo que é str
    input_str = str(input_str)

    # Normalizando o texto conforme a forma NFKD
    nfkd_form = unicodedata.normalize("NFKD", input_str)
    output_str = "".join([c for c in nfkd_form if not unicodedata.combining(c)])

    # Removendo as possíveis tags de HTML
    regex_tags = r"</?.>"
    output_str = re.sub(regex_tags, "", output_str)

    # Substituindo os caracteres especiais e números (tudo o que NÃO estiver de A-z)
    regex = re.compile(r"[^a-zA-Z0-9\s]+")
    tokens = regex.sub(" ", output_str).split()

    # Removendo possíveis espaços em branco no início e/ou fim da str
    output_str = " ".join(map(lambda x: x.strip(), tokens))

    # Retorna algo apenas se o resultado NÃO for uma str vazia
    return output_str.replace(" ", "_").upper()


# -----------------------------------------------------------------------------
# Lidando com colunas duplicadas
# -----------------------------------------------------------------------------


def rename_duplicates(input_list: List[str]) -> List[str]:
    # Count occurrences of each value in the list
    occurrences = Counter(input_list)
    # Initialize an empty list to store the result
    result = []
    # Dictionary to keep track of the renaming count for each value
    rename_count = {}
    for item in input_list:
        if occurrences[item] > 1:
            # If the item occurs more than once, rename it with the format "VALUE_{i}"
            if item in rename_count:
                rename_count[item] += 1
            else:
                rename_count[item] = 1
            new_name = f"{item}_{rename_count[item]}"
            result.append(new_name)
        else:
            # If the item is unique, keep it as is
            result.append(item)
    return result


# -----------------------------------------------------------------------------
# Função "principal" de empilhamento
# -----------------------------------------------------------------------------


def empilha_relatorios() -> None:
    print(
        """################################
### 🏗️ EMPILHANDO RELATÓRIOS ###
################################\n"""
    )
    for i, relatorio in enumerate(RELATORIOS, 1):
        t_0 = time()
        path_destino = DIR_DESTINO / f"{relatorio.nome.lower().replace(" ", "_")}.csv"
        if path_destino.exists():
            print(
                f"✅ ({i}/{len(RELATORIOS)}) Relatórios '{relatorio.nome}' já foram empilhados!\n"
            )
            continue
        print(
            f"⏳ ({i}/{len(RELATORIOS)}) Empilhando relatórios sobre '{relatorio.nome}' . . ."
        )
        arquivos = DIR_DADOS.glob(pattern=relatorio.regex)
        csv_empilhado = reduce(f_reduce, arquivos, None)
        with open(path_destino, "w", encoding="utf-8") as csv_f:
            csv_f.write(csv_empilhado)
        print(
            f"✅ Relatórios '{relatorio.nome}' empilhados com sucesso!\n🕐 Tempo: {t_0 - time():.4f} s\n"
        )
    return None
