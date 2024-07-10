from pathlib import Path
from time import time

from scraping_wto.controle_fluxo import (
    add_na_fila,
    consulta_ja_feita,
    erro_consulta,
    get_fila,
    log_consulta_realizada_sucesso,
    remove_da_fila,
)
from scraping_wto.selenium_utils import (
    navegador_firefox,
)
from scraping_wto.utils import extraindo_todos_arquivos, get_path_projeto
from scraping_wto.website_scraping import (
    download_consulta,
    get_info_ultima_consulta_pais,
    get_lista_paises,
    navegador_login,
)

DIR_PROJETO = get_path_projeto()
assert isinstance(DIR_PROJETO, Path)
DIR_DADOS_ZIP = DIR_PROJETO / "data/bronze/tl/zip"
DIR_DESTINO_DADOS = DIR_PROJETO / "data/bronze/tl"

URL_EXPORT = "https://tao.wto.org/ExportReport.aspx"


def main() -> None:
    print(
        """#############################
### 🤖 INÍCIO DO SCRAPING ###
#############################\n"""
    )

    t_ref_scraping = time()

    navegador = navegador_firefox(use_default_firefox_bin=False, headless=True)

    navegador_login(navegador=navegador)

    lista_web_element_pais = get_lista_paises(navegador=navegador)
    f_map = lambda web_element: web_element.text
    lista_paises = list(map(f_map, lista_web_element_pais))

    print(
        """\n################################
### 🔍 VERIFICANDO CONSULTAS ###
################################\n"""
    )

    t_ref_verificacao = time()

    for n, pais in enumerate(lista_paises, 1):
        print(f"\n({n}/{len(lista_paises)}) {pais.upper()}")
        ultimos_dados_disponiveis = get_info_ultima_consulta_pais(navegador, pais)
        if ultimos_dados_disponiveis is None:  # DEU ERRO! NoSuchElementException
            print(f"💀 DEU ERRO! NoSuchElementException para '{pais}'!")
            erro_consulta(pais)
        elif not consulta_ja_feita(
            ultimos_dados_disponiveis
        ):  # INSERIR NA LISTA DE CONSULTAS A SEREM FEITAS
            print(f"❌ Consulta para '{pais}' não foi feita. Adicionada à fila!")
            add_na_fila(ultimos_dados_disponiveis)
        else:  # Consulta já feita
            print(f"✅ Consulta para '{pais}' já foi feita!")

    print(
        """\n##################################
### ✅ CONSULTAS VERIFICADAS ! ###
##################################\n"""
    )

    tempo_verificacao_consultas = time() - t_ref_verificacao

    consultas = None if get_fila() == [] else get_fila()

    if consultas is None:
        navegador.close()
        t_ref_unzip = time()
        extraindo_todos_arquivos(
            dir_arquivos_zip=DIR_DADOS_ZIP, dir_destino=DIR_DESTINO_DADOS
        )
        print(
            f"""✅ Os dados estão atualizados, não há consultas a serem feitas!\n\n############################
### ⏱ Tempos de Execução ###
############################

> ⏱ Scraping: {t_ref_scraping + tempo_verificacao_consultas:.4f} s
\t> ⏱ Verificação consultas: {tempo_verificacao_consultas:.4f} s

> ⏱ Unzip dos arquivos: {time() - t_ref_unzip:.4f} s\n\n🏁 Código finalizado."""
        )
        return None

    navegador.get(URL_EXPORT)
    print(
        f"""\n################################
### 🛠️ REALIZANDO CONSULTAS! ###
################################

> Resta(m) {len(consultas)} consulta(s)"""
    )

    t_ref_consultas = time()

    while consultas is not None:
        consulta = consultas[0]
        print(f"\n🔍 Consultando dados para '{consulta.COUNTRY.upper()}' . . .\n")

        sucesso = download_consulta(navegador, consulta)

        if sucesso:
            remove_da_fila(consulta)
            log_consulta_realizada_sucesso(consulta)
            print(
                f"✅ CONSULTA REALIZADA COM SUCESSO!\n\n> Resta(m) {len(consultas) - 1} consulta(s)"
            )

        consultas = None if get_fila() == [] else get_fila()

    print(
        """\n#################################
### ✅ CONSULTAS REALIZADAS ! ###
#################################\n\n"""
    )

    tempo_consultas = time() - t_ref_consultas

    navegador.close()

    tempo_scraping = time() - t_ref_scraping

    print(
        """##########################
### 🤖 FIM DO SCRAPING ###
##########################\n"""
    )

    t_ref_unzip = time()
    extraindo_todos_arquivos(
        dir_arquivos_zip=DIR_DADOS_ZIP, dir_destino=DIR_DESTINO_DADOS
    )
    tempo_unzip = time() - t_ref_unzip

    print(
        f"""############################
### ⏱ Tempos de Execução ###
############################

> ⏱ Scraping: {tempo_scraping:.4f} s
\t> ⏱ Verificação consultas: {tempo_verificacao_consultas:.4f} s
\t> ⏱ Download relatórios: {tempo_consultas:.4f} s

> ⏱ Unzip dos arquivos: {tempo_unzip:.4f} s\n\n"""
    )

    print("🏁 Código finalizado.")

    return None


if __name__ == "__main__":
    main()
