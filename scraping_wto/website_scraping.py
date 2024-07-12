# =============================================================================
# BIBLIOTECAS E MÓDULOS
# =============================================================================

import re
import os
import pandas as pd
from pathlib import Path
from time import sleep
from typing import Callable, Optional, Tuple

import requests
from dotenv import find_dotenv, load_dotenv
from selenium.common import NoSuchElementException, TimeoutException
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from scraping_wto.controle_fluxo import (
    remove_da_fila,
    log_consulta_realizada_sucesso,
)
from scraping_wto.schemas import Consulta
from scraping_wto.selenium_utils import (
    clica_botao,
    espera_elemento_clicavel,
    espera_elemento_visivel,
    espera_presenca_elemento,
    insere_texto,
)
from scraping_wto.utils import (
    get_path_projeto,
    normaliza_nomes,
    tempo_espera_aleatorio,
    extrai_arquivo,
    extrai_nome_pais,
)

# =============================================================================
# CLASSES E SCHEMAS
# =============================================================================


class ScriptsJS:
    def __init__(self) -> None:
        return None

    @staticmethod
    def abre_query() -> str:
        return """let element = document.querySelector("#ctl00_qsl_lbChangeQuery");
element.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'nearest' });
element.click();"""

    @staticmethod
    def confirma_query() -> str:
        return """let element = document.querySelector("#ctl00_qsl_qs_pop_ctl00_bContinue");
element.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'nearest' });
element.click();"""

    @staticmethod
    def get_info_paises() -> str:
        return """tabelaInfosPais = document.querySelector("#ctl00_qsl_qs_pop_ctl00_dgYear");
linhaInfosPais = tabelaInfosPais.querySelectorAll("tr.GridItem")[0];
if (!linhaInfosPais) {
    return ["", "", ""];
} else {
    arrayInfosPais = [...linhaInfosPais.querySelectorAll("td")].slice(1);
    infosPais = arrayInfosPais.map(td => td.textContent);
    return infosPais;
}"""


# =============================================================================
# CONSTANTES
# =============================================================================

path_projeto = get_path_projeto()
assert isinstance(path_projeto, Path)
DIR_DOWNLOAD_ARQUIVOS = str(path_projeto / "data/bronze/tl/zip")
DIR_DESTINO_UNZIP = path_projeto / "data/bronze/tl"
JS_SCRIPTS = ScriptsJS()

# =============================================================================
# FUNÇÕES
# =============================================================================

# -----------------------------------------------------------------------------
# Faz o login na página da WTO
# -----------------------------------------------------------------------------


def navegador_login(navegador: WebDriver) -> None:
    """Retorna um navegador já na página inicial da WTO"""

    # Pegando as infos de login
    load_dotenv(find_dotenv())

    usuario = os.getenv("USUARIO_WTO")
    assert usuario is not None, "usuario is None"

    senha = os.getenv("SENHA_WTO")
    assert senha is not None, "senha is None"

    # Abrindo a página
    link_pagina = "https://tao.wto.org/welcome.aspx?ReturnUrl=%2fdefault.aspx"
    navegador.get(link_pagina)
    print("Página web aberta!")

    # Inserindo o usuário
    print("Inserindo o usuário. . .")
    localizador_usuario = ("xpath", '//*[@id="ctl00_c_ctrLogin_UserName"]')
    insere_texto(navegador, *localizador_usuario, usuario)

    # Inserindo a senha
    print("Inserindo a senha. . .")
    localizador_senha = ("xpath", '//*[@id="ctl00_c_ctrLogin_Password"]')
    insere_texto(navegador, *localizador_senha, senha)

    # Clicando no "lembre-se de mim"
    localizador_lembrar_de_mim = (
        "xpath",
        '//input[@id="ctl00_c_ctrLogin_RememberMe"]',
    )
    clica_botao(navegador, *localizador_lembrar_de_mim)

    # Clicando no "login"
    localizador_login = ("xpath", '//*[@id="ctl00_c_ctrLogin_LoginButton"]')
    clica_botao(navegador, *localizador_login)

    print("LOGIN REALIZADO!")
    tempo_espera_aleatorio()

    return None


# -----------------------------------------------------------------------------
# Seleciona um país para consultar <- JANELA DE CONSULTA
# -----------------------------------------------------------------------------


def clica_consulta_pais(navegador: WebDriver, pais: str) -> None:
    localizador_linha_pais = (
        "xpath",
        f"""//tr[(contains(@class, "GridItem") or contains(@class, "GridAlternatingItem")) and normalize-space()="{pais}"]//input""",
    )

    try:
        clica_botao(navegador, *localizador_linha_pais)
    except TimeoutException:
        print("Não achou o país")

    return None


# -----------------------------------------------------------------------------
# Retorna as informações dos dados mais recentes para consulta de um país
# -----------------------------------------------------------------------------


def get_info_ultima_consulta_pais(
    navegador: WebDriver, pais: str
) -> Optional[Consulta]:
    clica_consulta_pais(navegador, pais)
    year, imports, nomenclature = navegador.execute_script(
        script=JS_SCRIPTS.get_info_paises()
    )

    return Consulta(COUNTRY=pais, YEAR=year, IMPORTS=imports, NOMENCLATURE=nomenclature)


# -----------------------------------------------------------------------------
# Abre a janela de consultas
# -----------------------------------------------------------------------------


def abrindo_popup_query(navegador: WebDriver) -> None:
    """Abrindo a janela de Query"""

    print("Abrindo uma nova query . . .")
    localizador_nova_query = ("xpath", '//*[@id="ctl00_qsl_lbChangeQuery"]')
    clica_botao(navegador, *localizador_nova_query)

    return None


# -----------------------------------------------------------------------------
# Fecha a janela de consultas
# -----------------------------------------------------------------------------


def fechando_popup_query(navegador: WebDriver) -> None:
    """Clicando em 'continuar'"""

    print("Confirmando a query . . .")
    localizador_continue = (
        "xpath",
        '//*[@id="ctl00_qsl_qs_pop_ctl00_bContinue"]',
    )
    clica_botao(navegador, *localizador_continue)

    return None


# -----------------------------------------------------------------------------
# Espera o pop-up "Processing" sumir
# -----------------------------------------------------------------------------


def em_espera(navegador: WebDriver) -> None:
    localizador_em_progresso = (
        "css selector",
        "html body form#aspnetForm div#ctl00_UpdateProgressObject",
    )
    web_element_em_progresso = navegador.find_element(*localizador_em_progresso)

    while web_element_em_progresso.get_attribute("aria-hidden") == "false":
        web_element_em_progresso = navegador.find_element(*localizador_em_progresso)

    return None


# -----------------------------------------------------------------------------
# Retorna uma lista de WebElements dos países que estão na tabela de consulta
# -----------------------------------------------------------------------------


def get_lista_paises(navegador: WebDriver) -> list[WebElement]:
    localizador_tabela_paises = (
        "css selector",
        "#ctl00_qsl_qs_pop_ctl00_dgCountry",
    )
    localizador_linhas_tabela_paises = (
        "css selector",
        "tr.GridItem, tr.GridAlternatingItem",
    )

    try:
        navegador.find_element(*localizador_tabela_paises)
    except NoSuchElementException:
        abrindo_popup_query(navegador)

    em_espera(navegador)
    espera_elemento_visivel(navegador, *localizador_tabela_paises)

    lista_web_element_pais = navegador.find_element(
        *localizador_tabela_paises
    ).find_elements(*localizador_linhas_tabela_paises)

    return lista_web_element_pais


# -----------------------------------------------------------------------------
# Pega o link de download do relatório <- PRECISA ESTAR NA PÁG RELATÓRIOS
# -----------------------------------------------------------------------------


def clica_botao_refresh(navegador: WebDriver) -> Optional[Callable]:
    xpath_botao_reload = '//input[@id="ctl00_c_viewFile_dgExportFile_ctl02_bReload"]'
    localizador_botao_reload = ("xpath", xpath_botao_reload)

    try:
        sleep(5)
        _ = espera_elemento_clicavel(navegador, *localizador_botao_reload, 1)
        print("🕙 Arquivo ainda não está pronto para download . . .")
        clica_botao(navegador, *localizador_botao_reload)
        em_espera(navegador)
        return clica_botao_refresh(navegador)

    except:
        print("\n✅Arquivo pronto para download!\n")

    return None


# -----------------------------------------------------------------------------
# Pega o link de download do relatório <- PRECISA ESTAR NA PÁG RELATÓRIOS
# -----------------------------------------------------------------------------


def get_link_download_pais(navegador: WebDriver, pais: str) -> str:

    localizador_link_download = (
        "xpath",
        f'//*[@id="ctl00_c_viewFile_dgExportFile"]//a[contains(@href, "{normaliza_nomes(pais)}")]',
    )

    elemento_link = espera_presenca_elemento(navegador, *localizador_link_download)
    link_ = elemento_link.get_attribute("href")
    assert (
        link_ is not None
    ), f"💀 [!!! ERRO !!!]\nNão foi encontrado um link de download do {pais}!"

    return link_


# -----------------------------------------------------------------------------
# Faz o download de um arquivo a partir de uma URL para um determinado diretório
# -----------------------------------------------------------------------------


def download_arq(url_download: str, target_directory: str) -> Tuple[bool, str]:
    SUCESSO = 200

    # Define the image URL and the desired local file path
    file_name = url_download.split("/")[-1].replace("%20", "_")

    # Create the target directory if it doesn't exist
    Path(target_directory).mkdir(exist_ok=True, parents=True)

    path_arquivo = Path(target_directory) / file_name

    try:
        # Download the image data
        response = requests.get(url_download)

        # Check if the request was successful (status code 200)
        if response.status_code == SUCESSO:
            with open(path_arquivo, "wb") as f:
                f.write(response.content)
            print(f"✅ Arquivo salvo em: {path_arquivo}")
            return True, str(path_arquivo)
        else:
            print(f"❌ Download do arquivo falhou. Status code: {response.status_code}")
            return False, ""
    except requests.exceptions.Timeout:
        print(f"💀 TimeoutError: Download falhou: {url_download}")
        return False, ""


# -----------------------------------------------------------------------------
# Deleta apenas o relatório de UM país <- PRECISA ESTAR NA PÁGINA DE RELATÓRIOS
# -----------------------------------------------------------------------------


def deleta_relatorio_pais(navegador: WebDriver, pais: str) -> Optional[Callable]:
    localizador_linhas_tabela_paises = ("css selector", ".table2, .table3")
    elementos_linha = navegador.find_elements(*localizador_linhas_tabela_paises)

    nome_pais_normalizado = normaliza_nomes(pais)
    f_filter = lambda elemento: nome_pais_normalizado in elemento.text
    linha_pais = list(filter(f_filter, elementos_linha))

    if len(linha_pais) > 0:
        print("✅ Relatório encontrado!")
        linha_pais = linha_pais[0]
    else:
        print("❌ Relatório não encontrado!")
        return None

    localizador_botao_deletar = ("xpath", ".//input[contains(@id, 'bDelete')]")

    try:
        botao_deletar = linha_pais.find_element(*localizador_botao_deletar)
    except NoSuchElementException:
        print("💀 Botão de deletar não encontrado!")
        return None

    navegador.execute_script("arguments[0].scrollIntoView();", botao_deletar)
    navegador.execute_script("arguments[0].click();", botao_deletar)
    navegador.switch_to.alert.accept()
    em_espera(navegador)

    return deleta_relatorio_pais(navegador=navegador, pais=pais)


# -----------------------------------------------------------------------------
# Verifica se existem relatórios p download <- PRECISA ESTAR NA PÁG RELATÓRIOS
# -----------------------------------------------------------------------------


def existem_relatorios_na_fila(navegador: WebDriver) -> bool:
    localizador_linhas_tabela_paises = ("css selector", ".table2, .table3")
    if navegador.find_elements(*localizador_linhas_tabela_paises):
        return True
    return False


# -----------------------------------------------------------------------------
# Verifica se existe relatórios que não estão prontos <- PRECISA ESTAR NA PÁG RELATÓRIOS
# -----------------------------------------------------------------------------


def existe_botao_refresh(navegador: WebDriver) -> bool:
    localizador_linhas_tabela_paises = ("css selector", ".table2, .table3")
    regex = r".*zip.(?!.*Ready).*"

    elementos_linha = navegador.find_elements(*localizador_linhas_tabela_paises)

    for elemento in elementos_linha:
        if re.match(pattern=regex, string=elemento.text):
            return True

    return False


# -----------------------------------------------------------------------------
# Deleta TODOS os relatórios <- PRECISA ESTAR NA PÁGINA DE RELATÓRIOS
# -----------------------------------------------------------------------------


def deleta_todos_relatorios(navegador: WebDriver) -> None:
    localizador_botao_deletar = ("xpath", ".//input[contains(@id, 'bDelete')]")
    while navegador.find_elements(*localizador_botao_deletar):
        clica_botao(navegador, *localizador_botao_deletar)
        navegador.switch_to.alert.accept()
        em_espera(navegador)
    return None


# -----------------------------------------------------------------------------
# Fluxo completo para download de uma consulta
# -----------------------------------------------------------------------------


def download_consulta(navegador: WebDriver, consulta: Consulta) -> None:

    # -----------------------------------------------------------------------------
    # 1 Abrindo a página de relatórios
    # -----------------------------------------------------------------------------

    navegador.get("https://tao.wto.org/ExportReport.aspx")

    # -----------------------------------------------------------------------------
    # 2 Verificando se existem relatórios na fila. SE SIM -> deleta
    # -----------------------------------------------------------------------------

    if existem_relatorios_na_fila(navegador):
        while existe_botao_refresh(navegador):
            clica_botao_refresh(navegador)
        deleta_todos_relatorios(navegador)

    # -----------------------------------------------------------------------------
    # 3 Selecionando o país a ser consultado
    # -----------------------------------------------------------------------------

    abrindo_popup_query(navegador)
    em_espera(navegador)

    print("Selecionando o país . . .")

    # Esperando o elemento ficar visivel
    localizador_tabela_paises = ("css selector", "#ctl00_qsl_qs_pop_ctl00_dgCountry")
    _ = espera_elemento_visivel(navegador, *localizador_tabela_paises)

    clica_consulta_pais(navegador, consulta.COUNTRY)
    em_espera(navegador)

    fechando_popup_query(navegador)
    em_espera(navegador)

    # -----------------------------------------------------------------------------
    # 4 Inserindo as informações
    # -----------------------------------------------------------------------------

    tempo_espera_aleatorio()
    print("\nInserindo informações . . .")

    # Selecionando o tipo de relatório

    print("(1/4) Escolhendo o tipo de relatório")
    localizador_dropdown = ("xpath", '//*[@id="ctl00_c_drpReport"]')
    botao_tipo_relatorio_dropdown = espera_elemento_visivel(
        navegador, *localizador_dropdown
    )
    botao_tipo_relatorio_dropdown.click()

    try:
        localizador_tl = ("xpath", "//option[contains(@value, 'TL')]")
        botao_tipo_relatorio = espera_elemento_visivel(navegador, *localizador_tl, 1)
        botao_tipo_relatorio.click()
        em_espera(navegador)
    except TimeoutException:
        raise Exception("NÃO EXISTE TL PARA ESTE PAÍS!")

    # Selecionando o formato do relatório

    print("(2/4) Escolhendo o formato de relatório")
    localizador_dropdown = ("xpath", '//*[@id="ctl00_c_pickFile_ddFormat"]')
    botao_dropdown = espera_elemento_clicavel(navegador, *localizador_dropdown)
    navegador.execute_script("arguments[0].value = 'txt';", botao_dropdown)

    em_espera(navegador)

    # Inserindo o nome do arquivo

    print("(3/4) Inserindo o nome do arquivo")
    localizador_nome_arquivo = ("xpath", '//*[@id="ctl00_c_pickFile_txtFileName"]')
    insere_texto(
        navegador, *localizador_nome_arquivo, normaliza_nomes(consulta.COUNTRY)
    )

    # Clicando em exportar

    print("(4/4) Clicando em exportar relatório\n")
    localizador_export = ("xpath", '//*[@id="ctl00_c_pickFile_btnExport"]')
    clica_botao(navegador, *localizador_export)

    em_espera(navegador)

    # -----------------------------------------------------------------------------
    # 5 Clicando no botão de refresh
    # -----------------------------------------------------------------------------

    while existe_botao_refresh(navegador):
        clica_botao_refresh(navegador)

    # -----------------------------------------------------------------------------
    # 6 Fazendo download
    # -----------------------------------------------------------------------------

    link_download = get_link_download_pais(navegador, consulta.COUNTRY)
    download_sucesso, path_arquivo_download = download_arq(
        url_download=link_download,
        target_directory=DIR_DOWNLOAD_ARQUIVOS,
    )

    if not download_sucesso:
        raise Exception("O DOWNLOAD NÃO FOI BEM-SUCEDIDO!")

    # -----------------------------------------------------------------------------
    # 7 Extraindo o arquivo
    # -----------------------------------------------------------------------------

    extrai_arquivo(Path(path_arquivo_download), DIR_DESTINO_UNZIP)

    # -----------------------------------------------------------------------------
    # 8 Verificando se o conteúdo do arquivo é o mesmo do que foi consultado
    # -----------------------------------------------------------------------------

    df_arquivo = pd.read_csv(
        DIR_DESTINO_UNZIP / f"{normaliza_nomes(consulta.COUNTRY)}_DutyDetails_TL.txt",
        sep="\t",
        dtype=str,
    )
    nome_pais_no_arquivo_unzip = normaliza_nomes(df_arquivo.loc[0, "Reporter"])
    nome_pais_no_arquivo_zip = extrai_nome_pais(path_arquivo_download)

    if nome_pais_no_arquivo_unzip != nome_pais_no_arquivo_zip:
        raise Exception("DADOS DE DOWNLOAD SÃO DIFERENTES DOS DADOS CONSULTADOS!")

    # -----------------------------------------------------------------------------
    # 8.1 CASO NÃO SEJA: DELETAR ARQUIVO > RECOMEÇAR A PESQUISA
    # -----------------------------------------------------------------------------

    # -----------------------------------------------------------------------------
    # 9 Colocando na lista de consultas realizadas com sucesso
    # -----------------------------------------------------------------------------

    remove_da_fila(consulta)
    log_consulta_realizada_sucesso(consulta)

    return None
