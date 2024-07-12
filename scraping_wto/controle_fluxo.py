# =============================================================================
# BIBLIOTECAS E MÓDULOS
# =============================================================================

import pickle
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd

from scraping_wto.schemas import Consulta
from scraping_wto.utils import get_path_projeto

# =============================================================================
# CONSTANTES
# =============================================================================

path_projeto = get_path_projeto()
assert isinstance(path_projeto, Path)


FORMATO_DATA = "%Y-%m-%d"
PATH_LOG_CONSULTAS_FEITAS = path_projeto / "log/consultas_feitas.csv"
PATH_LOG_ERRO_CONSULTA = path_projeto / "log/consultas_erros.csv"
PATH_CONSULTAS_A_SEREM_FEITAS = path_projeto / "temp/consultas_a_fazer.pkl"

# =============================================================================
# FUNÇÕES
# =============================================================================


# -----------------------------------------------------------------------------
# Verifica se a consulta está no registro de consultas feitas
# -----------------------------------------------------------------------------


def consulta_ja_feita(consulta: Consulta) -> bool:
    df_log = (
        pd.read_csv(PATH_LOG_CONSULTAS_FEITAS, sep=";").drop(columns=["DATA_CONSULTA"])
        if Path(PATH_LOG_CONSULTAS_FEITAS).exists()
        else pd.DataFrame(
            columns=[
                "COUNTRY",
                "YEAR",
                "IMPORTS",
                "NOMENCLATURE",
                "DATA_CONSULTA",
            ]
        )
    )

    consultas_feitas = (
        Consulta(**consulta_feita.to_dict()) for _, consulta_feita in df_log.iterrows()
    )

    if consulta in consultas_feitas:
        data_consulta_log = df_log[df_log["COUNTRY"] == consulta.COUNTRY].iloc[0, 1]
        if data_consulta_log < consulta.YEAR:
            return False
        return True
    return False


# -----------------------------------------------------------------------------
# Registra quando deu um problema grave durante uma consulta
# -----------------------------------------------------------------------------


def erro_consulta(pais: str) -> None:
    Path(PATH_LOG_ERRO_CONSULTA).parent.mkdir(exist_ok=True, parents=True)

    data_consulta = datetime.now().strftime(format=FORMATO_DATA)

    df_log = (
        pd.read_csv(PATH_LOG_ERRO_CONSULTA, sep=";").drop(columns=["DATA_CONSULTA"])
        if Path(PATH_LOG_ERRO_CONSULTA).exists()
        else pd.DataFrame(
            data=[[pais, data_consulta]], columns=["COUNTRY", "DATA_CONSULTA"]
        )
    )

    df_log.to_csv(PATH_LOG_ERRO_CONSULTA, sep=";", index=False)

    return None


# -----------------------------------------------------------------------------
# Retorna a lista de consultas que precisam ser feitas
# -----------------------------------------------------------------------------


def get_fila() -> Optional[list[Consulta]]:
    if Path(PATH_CONSULTAS_A_SEREM_FEITAS).exists():
        with open(PATH_CONSULTAS_A_SEREM_FEITAS, "rb") as pkl_f:
            consultas = pickle.load(file=pkl_f)
        return consultas
    return None


# -----------------------------------------------------------------------------
# Adiciona uma consulta na fila de consultas a serem feitas
# -----------------------------------------------------------------------------


def add_na_fila(consulta: Consulta) -> None:
    Path(PATH_CONSULTAS_A_SEREM_FEITAS).parent.mkdir(exist_ok=True, parents=True)

    consultas = [] if get_fila() is None else get_fila()
    assert consultas is not None, "consultas is None"

    if consulta not in consultas:
        consultas.append(consulta)
        with open(PATH_CONSULTAS_A_SEREM_FEITAS, "wb") as pkl_f:
            pickle.dump(file=pkl_f, obj=consultas)

    return None


# -----------------------------------------------------------------------------
# Remove uma consulta da fila <- geralmente é porque deu tudo certo
# -----------------------------------------------------------------------------


def remove_da_fila(consulta: Consulta) -> None:
    consultas = get_fila()

    if consultas is None:
        return None

    consultas.remove(consulta)

    with open(PATH_CONSULTAS_A_SEREM_FEITAS, "wb") as pkl_f:
        pickle.dump(file=pkl_f, obj=consultas)

    return None


# -----------------------------------------------------------------------------
# Add uma consulta no log de "consultas realizadas com sucesso"
# -----------------------------------------------------------------------------


def log_consulta_realizada_sucesso(consulta: Consulta) -> None:
    Path(PATH_LOG_CONSULTAS_FEITAS).parent.mkdir(exist_ok=True, parents=True)

    data_consulta = datetime.now().strftime(format=FORMATO_DATA)

    consulta_dict = consulta.model_dump()
    consulta_dict.update({"DATA_CONSULTA": data_consulta})
    linha_consulta = [consulta_dict]

    df_log = (
        pd.read_csv(PATH_LOG_CONSULTAS_FEITAS, sep=";")
        if Path(PATH_LOG_CONSULTAS_FEITAS).exists()
        else pd.DataFrame(
            columns=[
                "COUNTRY",
                "YEAR",
                "IMPORTS",
                "NOMENCLATURE",
                "DATA_CONSULTA",
            ]
        )
    )

    if consulta.COUNTRY in df_log["COUNTRY"].values:
        df_log = df_log[df_log["COUNTRY"] != consulta.COUNTRY].reset_index(drop=True)

    df_log = df_log._append(linha_consulta, ignore_index=True).sort_values(by="COUNTRY")

    df_log.to_csv(PATH_LOG_CONSULTAS_FEITAS, sep=";", index=False)

    return None
