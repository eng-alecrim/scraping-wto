# =============================================================================
# BIBLIOTECAS E MÓDULOS
# =============================================================================

import logging
import logging.config
import pickle
from pathlib import Path

from scraping_wto.selenium_utils import navegador_firefox
from scraping_wto.website_scraping import (
    confere_dados_consulta_pais,
    download_consulta,
    get_lista_paises,
    navegador_login,
)

# =============================================================================
# CONSTANTES
# =============================================================================

# -----------------------------------------------------------------------------
# Configurando o navegador
# -----------------------------------------------------------------------------

USAR_FIREFOX_PADRAO = False
HEADLESS = True

# -----------------------------------------------------------------------------
# Configurando o logger
# -----------------------------------------------------------------------------

logging.config.fileConfig("config/logging.toml")
LOGGER = logging.getLogger("logMain.info.debug")

# -----------------------------------------------------------------------------
# Paths
# -----------------------------------------------------------------------------

PATH_FILA_CONSULTAS = Path("temp/consultas_a_fazer.pkl")

# =============================================================================
# FUNÇÕES
# =============================================================================

# -----------------------------------------------------------------------------
# Verifica se a fila de consultas está vazia
# -----------------------------------------------------------------------------


def fila_vazia() -> bool:
    with open(PATH_FILA_CONSULTAS, "rb") as pkl_f:
        consultas_existentes = pickle.load(pkl_f)
    if consultas_existentes:
        return False
    return True


# -----------------------------------------------------------------------------
# Loop que realiza o download dos dados para cada país na fila
# -----------------------------------------------------------------------------


def loop_consulta() -> None:
    navegador = navegador_firefox(
        use_default_firefox_bin=USAR_FIREFOX_PADRAO, headless=HEADLESS
    )
    navegador_login(navegador=navegador)

    with open(PATH_FILA_CONSULTAS, "rb") as pkl_f:
        consultas_existentes = pickle.load(pkl_f)

    LOGGER.info(f"loop_consulta: {len(consultas_existentes)} consultas na fila.")
    for n, consulta in enumerate(consultas_existentes, 1):
        LOGGER.debug(
            f"loop_consulta: ({n}/{len(consultas_existentes)}) '{consulta.COUNTRY.upper()}'"
        )
        try:
            download_consulta(navegador=navegador, consulta=consulta)
        except Exception as e:
            LOGGER.warning(
                f"loop_consulta: Erro consulta para país '{consulta.COUNTRY}': {e}"
            )

    navegador.close()

    return None


# =============================================================================
# CÓDIGO
# =============================================================================


def main() -> None:

    # -----------------------------------------------------------------------------
    # Verificando se existe uma fila pré-existente de consultas
    # -----------------------------------------------------------------------------

    LOGGER.info(
        "main: Verificando se existem consultas já existentes a serem realizadas."
    )
    if PATH_FILA_CONSULTAS.exists() and not fila_vazia():
        LOGGER.info("main: Existe uma fila já existente. Realizando consultas . . .")
        loop_consulta()
        LOGGER.info("main: Consultas realizadas.")
    else:
        LOGGER.info("main: Não existem consultas pendentes.")

    # -----------------------------------------------------------------------------
    # Abrindo o navegador
    # -----------------------------------------------------------------------------

    navegador = navegador_firefox(
        use_default_firefox_bin=USAR_FIREFOX_PADRAO, headless=HEADLESS
    )
    LOGGER.info("main: Navegador aberto.")

    # -----------------------------------------------------------------------------
    # Fazendo login na WTO
    # -----------------------------------------------------------------------------

    navegador_login(navegador=navegador)
    LOGGER.info("main: Login feito.")

    # -----------------------------------------------------------------------------
    # Obtendo a lista de países disponíveis para consulta
    # -----------------------------------------------------------------------------

    lista_web_element_pais = get_lista_paises(navegador=navegador)
    lista_paises = list(
        map(lambda web_element: web_element.text, lista_web_element_pais)
    )
    LOGGER.info("main: Lista de países obtida.")

    # -----------------------------------------------------------------------------
    # Fazendo a verificação da consulta para cada país
    # -----------------------------------------------------------------------------

    LOGGER.info("main: Conferindo dados disponíveis para consulta de cada país.")
    for n, pais in enumerate(lista_paises, 1):
        LOGGER.debug(f"main: ({n}/{len(lista_paises)}) '{pais.upper()}'")
        try:
            confere_dados_consulta_pais(navegador=navegador, pais=pais)
        except Exception as e:
            LOGGER.warning(f"main: Erro de execução para o país '{pais}': {e}.")
            print(e)
    LOGGER.info("main: Consultas verificadas.")

    # -----------------------------------------------------------------------------
    # Fechando o navegador
    # -----------------------------------------------------------------------------

    navegador.close()
    LOGGER.info("main: Navegador fechado.")

    # -----------------------------------------------------------------------------
    # Verificando se existe uma fila de consultas
    # -----------------------------------------------------------------------------

    if PATH_FILA_CONSULTAS.exists() and not fila_vazia():
        LOGGER.info("main: Realizando consultas na fila . . .")
        loop_consulta()
        LOGGER.info("main: Consultas realizadas.")
    else:
        LOGGER.info("main: Não existem consultas pendentes.")

    # -----------------------------------------------------------------------------
    # Finalizando o código
    # -----------------------------------------------------------------------------

    LOGGER.info("main: Fim do código.")

    return None


if __name__ == "__main__":
    main()
