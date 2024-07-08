import os
from pathlib import Path
from time import sleep
from typing import Callable, Optional

import requests
from dotenv import find_dotenv, load_dotenv
from selenium.common import NoSuchElementException
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from scraping_wto.controle_fluxo import get_fila, remove_da_fila
from scraping_wto.schemas import Consulta
from scraping_wto.selenium_utils import (
    clica_botao,
    espera_elemento_clicavel,
    espera_elemento_visivel,
)
from scraping_wto.utils import normaliza_nomes, tempo_espera_aleatorio

DIR_DOWNLOAD_ARQUIVOS = "data/bronze/tl"


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


JS_SCRIPTS = ScriptsJS()


def navegador_login(navegador: WebDriver) -> None:
    """Retorna um navegador já na página inicial da WTO"""

    # Pegando as infos de login
    load_dotenv(find_dotenv())

    usuario = os.getenv("USUARIO_WTO")
    senha = os.getenv("SENHA_WTO")

    # Abrindo a página
    link_pagina = "https://tao.wto.org/welcome.aspx?ReturnUrl=%2fdefault.aspx"
    navegador.get(link_pagina)
    print("Página web aberta!")

    # Inserindo o usuário
    xpath_usuario = '//*[@id="ctl00_c_ctrLogin_UserName"]'
    navegador.execute_script(
        f"document.evaluate('{xpath_usuario}', document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue.value = '{usuario}';"
    )
    print("Inserindo o usuário. . .")

    # Inserindo a senha
    xpath_password = '//*[@id="ctl00_c_ctrLogin_Password"]'
    navegador.execute_script(
        f"document.evaluate('{xpath_password}', document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue.value = '{senha}';"
    )
    print("Inserindo a senha. . .")

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


def clica_consulta_pais(navegador: WebDriver, pais: str) -> None:
    xpath = f"""//tr[(contains(@class, "GridItem") or contains(@class, "GridAlternatingItem")) and normalize-space()="{pais}"]"""

    try:
        web_element_pais = navegador.find_element(by="xpath", value=xpath)
    except NoSuchElementException:
        return None

    elemento_clicavel = web_element_pais.find_element(by="tag name", value="input")
    navegador.execute_script("arguments[0].scrollIntoView(true);", elemento_clicavel)
    sleep(0.5)
    elemento_clicavel.click()
    sleep(1)

    return None


def get_info_ultima_consulta_pais(
    navegador: WebDriver, pais: str
) -> Optional[Consulta]:
    clica_consulta_pais(navegador, pais)
    year, imports, nomenclature = navegador.execute_script(
        script=JS_SCRIPTS.get_info_paises()
    )

    return Consulta(COUNTRY=pais, YEAR=year, IMPORTS=imports, NOMENCLATURE=nomenclature)


def abrindo_popup_query(navegador: WebDriver) -> None:
    """Abrindo a janela de Query"""

    print("Abrindo uma nova query . . .")
    localizador_nova_query = ("xpath", '//*[@id="ctl00_qsl_lbChangeQuery"]')
    clica_botao(navegador, *localizador_nova_query)

    return None


def fechando_popup_query(navegador: WebDriver) -> None:
    """Clicando em 'continuar'"""

    print("Confirmando a query . . .")
    localizador_continue = (
        "xpath",
        '//*[@id="ctl00_qsl_qs_pop_ctl00_bContinue"]',
    )
    clica_botao(navegador, *localizador_continue)

    return None


def em_espera(navegador: WebDriver) -> None:
    localizador_em_progresso = (
        "css selector",
        "html body form#aspnetForm div#ctl00_UpdateProgressObject",
    )
    web_element_em_progresso = navegador.find_element(*localizador_em_progresso)

    while web_element_em_progresso.get_attribute("aria-hidden") == "false":
        web_element_em_progresso = navegador.find_element(*localizador_em_progresso)

    return None


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


def seleciona_pais(navegador: WebDriver, nome_pais: str) -> None:
    # Bibliotecas

    abrindo_popup_query(navegador)
    em_espera(navegador)

    print("Selecionando o país . . .")

    # Selecionando um país
    lista_web_element_pais = get_lista_paises(navegador)

    dict_web_element_pais = {
        elemento.text: elemento.find_element("tag name", "input")
        for elemento in lista_web_element_pais
    }

    botao_pais = dict_web_element_pais[nome_pais]

    navegador.execute_script("arguments[0].scrollIntoView();", botao_pais)
    navegador.execute_script("arguments[0].click();", botao_pais)

    fechando_popup_query(navegador)
    em_espera(navegador)

    return None


def clica_tipo_relatorio(navegador: WebDriver) -> bool:
    # Bibliotecas

    em_espera(navegador)
    localizador_dropdown = ("xpath", '//*[@id="ctl00_c_drpReport"]')
    espera_elemento_clicavel(navegador, *localizador_dropdown)
    navegador.find_element(*localizador_dropdown).click()

    localizador_tl = ("xpath", "//option[contains(@value, 'TL')]")

    try:
        _ = navegador.find_element(*localizador_tl)
    except NoSuchElementException:
        print("NÃO EXISTE TL PARA ESTE PAÍS!")
        return False

    espera_elemento_clicavel(navegador, *localizador_tl)
    navegador.find_element(*localizador_tl).click()

    return True


def clica_formato_arquivo(navegador: WebDriver) -> None:
    # Bibliotecas

    em_espera(navegador)
    localizador_dropdown = ("xpath", '//*[@id="ctl00_c_pickFile_ddFormat"]')
    espera_elemento_clicavel(navegador, *localizador_dropdown)
    botao_dropdown = navegador.find_element(*localizador_dropdown)
    navegador.execute_script("arguments[0].value = 'txt';", botao_dropdown)

    return None


def info_report_export(navegador: WebDriver, pais: str) -> None:
    print("\nInserindo informações . . .")

    # Selecionando o tipo de relatório
    print("(1/4) Escolhendo o tipo de relatório")
    existe_relatorio = clica_tipo_relatorio(navegador)

    if not existe_relatorio:
        print("\n\t❌NÃO EXISTE RELATÓRIO TL PARA ESTE PAÍS!\n")
        f_filter = lambda consulta: consulta.COUNTRY == pais
        consulta = next(filter(f_filter, get_fila()))
        remove_da_fila(consulta)
        return None

    tempo_espera_aleatorio()

    # Selecionando o formato do relatório
    print("(2/4) Escolhendo o formato de relatório")
    clica_formato_arquivo(navegador)

    tempo_espera_aleatorio()

    # Inserindo o nome do arquivo
    print("(3/4) Inserindo o nome do arquivo")
    xpath_nome_arq = '//*[@id="ctl00_c_pickFile_txtFileName"]'
    espera_elemento_visivel(navegador, "xpath", xpath_nome_arq)
    navegador.execute_script(
        f"""document.evaluate('{xpath_nome_arq}', document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue.value = '{normaliza_nomes(pais)}';"""
    )

    tempo_espera_aleatorio()

    # Clicando em exportar
    print("(4/4) Clicando em exportar relatório\n")
    localizador_export = ("xpath", '//*[@id="ctl00_c_pickFile_btnExport"]')
    clica_botao(navegador, *localizador_export)

    return None


def clica_botao_refresh(navegador: WebDriver) -> Optional[Callable]:
    xpath_botao_reload = '//input[@id="ctl00_c_viewFile_dgExportFile_ctl02_bReload"]'
    localizador_botao_reload = ("xpath", xpath_botao_reload)

    elemento_botao_reload = navegador.find_elements(*localizador_botao_reload)

    if len(elemento_botao_reload) > 0:
        print("🕙 Arquivo ainda não está pronto para download . . .")
        navegador.execute_script(
            f"document.evaluate('{xpath_botao_reload}', document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue.scrollIntoView();"
        )
        navegador.execute_script(
            f"document.evaluate('{xpath_botao_reload}', document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue.click();"
        )

        sleep(5)

        return clica_botao_refresh(navegador=navegador)

    print("\n✅Arquivo pronto para download!\n")

    return None


def get_link_download_pais(navegador: WebDriver, pais: str) -> str:
    nome_pais_normalizado = normaliza_nomes(pais)

    localizador_tabela_relatorios = (
        "xpath",
        '//*[@id="ctl00_c_viewFile_dgExportFile"]',
    )
    webelemnt_tabela_relatorios = navegador.find_element(*localizador_tabela_relatorios)

    localizaodr_link_download = (
        "xpath",
        f"//a[contains(@href, '{nome_pais_normalizado}')]",
    )
    elemento_link = webelemnt_tabela_relatorios.find_element(*localizaodr_link_download)

    link_ = elemento_link.get_attribute("href")

    assert (
        link_ is not None
    ), f"💀 [!!! ERRO !!!]\nNão foi encontrado um link de download do {pais}!"

    return link_


def download_arq(url_download: str, target_directory: str) -> bool:
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
            return True
        else:
            print(f"❌ Download do arquivo falhou. Status code: {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"💀 TimeoutError: Download falhou: {url_download}")
        return False


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


def download_consulta(navegador: WebDriver, consulta_a_ser_feita: Consulta) -> bool:
    try:
        seleciona_pais(navegador, consulta_a_ser_feita.COUNTRY)
        info_report_export(navegador, consulta_a_ser_feita.COUNTRY)
        tempo_espera_aleatorio()
        clica_botao_refresh(navegador)
        link_download = get_link_download_pais(navegador, consulta_a_ser_feita.COUNTRY)

        fez_download = False
        contador_fracasso = 0
        MAX_TENTATIVAS = 10
        while fez_download is False:
            if contador_fracasso > MAX_TENTATIVAS:
                navegador.close()
                raise ValueError("💀 NÃO FOI POSSÍVEL FAZER O DOWNLOAD!")
            fez_download = download_arq(link_download, DIR_DOWNLOAD_ARQUIVOS)
            if fez_download is False:
                contador_fracasso += 1
                tempo_espera_aleatorio()
                navegador.refresh()

        deleta_relatorio_pais(navegador, consulta_a_ser_feita.COUNTRY)

        return True
    except Exception as e:
        print(f"DEU ERRO!\n{e}")
        return False
