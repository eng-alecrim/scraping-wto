from scraping_wto.selenium_utils import navegador_firefox
from scraping_wto.website_scraping import (
    navegador_login,
    get_lista_paises,
    get_info_ultima_consulta_pais,
)
from scraping_wto.controle_fluxo import erro_consulta, consulta_ja_feita, add_na_fila

print(
    """#############################
### 🤖 INÍCIO DO SCRAPING ###
#############################\n"""
)


navegador = navegador_firefox(use_default_firefox_bin=False, headless=False)

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
