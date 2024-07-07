URL_EXPORT = "https://tao.wto.org/ExportReport.aspx"


def main() -> None:
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
        navegador_login,
        get_lista_paises,
        get_info_ultima_consulta_pais,
    )

    navegador = navegador_firefox(use_default_firefox_bin=False, headless=True)

    navegador_login(navegador=navegador)

    lista_web_element_pais = get_lista_paises(navegador=navegador)
    f_map = lambda web_element: web_element.text
    lista_paises = list(map(f_map, lista_web_element_pais))

    for pais in lista_paises:
        ultimos_dados_disponiveis = get_info_ultima_consulta_pais(navegador, pais)
        if ultimos_dados_disponiveis is None:
            # DEU ERRO! NoSuchElementException
            erro_consulta(pais)
        if not consulta_ja_feita(ultimos_dados_disponiveis):
            # INSERIR NA LISTA DE CONSULTAS A SEREM FEITAS
            add_na_fila(ultimos_dados_disponiveis)

    consultas = get_fila()

    if consultas is not None:
        navegador.get(URL_EXPORT)

    while consultas is not None:
        consulta = consultas[0]

        sucesso = download_consulta(navegador, consulta)

        if sucesso:
            remove_da_fila(consulta)
            log_consulta_realizada_sucesso(consulta)

        consultas = get_fila()

    navegador.close()

    return None


if __name__ == "__main__":
    main()
