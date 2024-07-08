from scraping_wto.controle_fluxo import (
    add_na_fila,
    consulta_ja_feita,
    erro_consulta,
    get_fila,
    log_consulta_realizada_sucesso,
    remove_da_fila,
)
from scraping_wto.selenium_utils import navegador_firefox
from scraping_wto.website_scraping import (
    download_consulta,
    get_info_ultima_consulta_pais,
    get_lista_paises,
    navegador_login,
)

URL_EXPORT = "https://tao.wto.org/ExportReport.aspx"


def main() -> None:
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

    for n, pais in enumerate(lista_paises, 1):
        print(f"\n({n}/{len(lista_paises)}) {pais.upper()}")
        ultimos_dados_disponiveis = get_info_ultima_consulta_pais(
            navegador, pais
        )
        if (
            ultimos_dados_disponiveis is None
        ):  # DEU ERRO! NoSuchElementException
            print(f"💀 DEU ERRO! NoSuchElementException para '{pais}'!")
            erro_consulta(pais)
        elif not consulta_ja_feita(
            ultimos_dados_disponiveis
        ):  # INSERIR NA LISTA DE CONSULTAS A SEREM FEITAS
            print(
                f"❌ Consulta para '{pais}' não foi feita. Adicionada à fila!"
            )
            add_na_fila(ultimos_dados_disponiveis)
        else:  # Consulta já feita
            print(f"✅ Consulta para '{pais}' já foi feita!")

    print(
        """\n##################################
### ✅ CONSULTAS VERIFICADAS ! ###
##################################\n"""
    )

    consultas = None if get_fila() == [] else get_fila()

    if consultas is None:
        navegador.close()
        print(
            "✅ Os dados estão atualizados, não há consultas a serem feitas!\n\n🏁 Código finalizado."
        )
        return None

    navegador.get(URL_EXPORT)
    print(
        f"""\n################################
### 🛠️ REALIZANDO CONSULTAS! ###
################################

> Resta(m) {len(consultas)} consulta(s)"""
    )

    while consultas is not None:
        consulta = consultas[0]
        print(
            f"\n🔍 Consultando dados para '{consulta.COUNTRY.upper()}' . . .\n"
        )

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

    navegador.close()

    print("🏁 Código finalizado.")

    return None


if __name__ == "__main__":
    main()
