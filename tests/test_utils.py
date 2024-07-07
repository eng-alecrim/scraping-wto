from scraping_wto.utils import get_path_projeto

NOME_PROJETO = "scraping-wto"


def test_get_path_projeto() -> None:

    assert get_path_projeto().name == NOME_PROJETO

    return None
