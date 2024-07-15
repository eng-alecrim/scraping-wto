# =============================================================================
# BIBLIOTECAS E MÓDULOS
# =============================================================================

import logging
import logging.config
import subprocess
from pathlib import Path

import requests
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as GeckoService
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from scraping_wto.utils import get_path_projeto

# =============================================================================
# CONSTANTES
# =============================================================================

DIR_PROJETO = get_path_projeto()
assert isinstance(DIR_PROJETO, Path)

logging.config.fileConfig(DIR_PROJETO / "config/logging.toml")
LOGGER = logging.getLogger("logMain.info.debug")

# =============================================================================
# FUNÇÕES
# =============================================================================

# -----------------------------------------------------------------------------
# Faz download do geckdriver, caso precise
# -----------------------------------------------------------------------------


def download_geckodriver(
    url_download: str = "https://github.com/mozilla/geckodriver/releases/download/v0.34.0/geckodriver-v0.34.0-linux64.tar.gz",
) -> None:
    dir_projeto = get_path_projeto()
    assert isinstance(dir_projeto, Path)

    nome_arquivo = url_download.split("/")[-1]
    path_download = dir_projeto / f"bin/{nome_arquivo}"

    if not path_download.parent.exists():
        path_download.parent.mkdir(parents=True, exist_ok=True)

    if path_download.exists():
        LOGGER.debug(f"download_geckodriver: {path_download} já existe!")
        return None

    with open(path_download, "wb") as download_f:
        response = requests.get(url_download)
        download_f.write(response.content)

    return None


# -----------------------------------------------------------------------------
# Retorna um WebDriver do Firefox via Selenium
# -----------------------------------------------------------------------------


def navegador_firefox(
    use_default_firefox_bin: bool = True, headless: bool = True
) -> WebDriver:
    def get_firefox_binary_path() -> str:
        """Returns the path to the Firefox binary."""

        try:
            result = subprocess.run(
                ["which", "firefox"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            raise FileNotFoundError(
                "Firefox binary not found. Please ensure Firefox is installed and available in the PATH."
            )

    dir_projeto = get_path_projeto()
    assert isinstance(dir_projeto, Path)
    path_download = dir_projeto / "data/bronze/download_browser"
    path_download.mkdir(exist_ok=True, parents=True)
    path_geckodriver = dir_projeto / "bin/geckodriver"

    firefox_options = webdriver.FirefoxOptions()
    firefox_options.add_argument("--no-sandbox")
    if not use_default_firefox_bin:
        firefox_options.binary_location = get_firefox_binary_path()
    if headless:
        firefox_options.add_argument("--headless")
    firefox_options.add_argument("--disable-dev-shm-usage")
    firefox_options.add_argument("--disable-dev-shm-using")
    firefox_options.add_argument("disable-infobars")
    firefox_options.add_argument("--window-size=1920,1080")
    firefox_options.set_preference("browser.download.folderList", 2)
    firefox_options.set_preference("browser.download.manager.showWhenStarting", False)
    firefox_options.set_preference(
        "browser.download.dir", str(path_download.absolute())
    )
    firefox_options.set_preference(
        "browser.helperApps.neverAsk.saveToDisk", "application/octet-stream"
    )
    firefox_options.set_preference("dom.webnotifications.enabled", False)
    firefox_options.set_preference("browser.tabs.warnOnClose", False)

    navegador = webdriver.Firefox(
        service=GeckoService(executable_path=str(path_geckodriver.absolute())),
        options=firefox_options,
    )

    return navegador


# -----------------------------------------------------------------------------
# Espera que um elemento web esteja visível antes de retorná-lo
# -----------------------------------------------------------------------------


def espera_elemento_visivel(
    navegador: WebDriver, by: str, value: str, timeout: int = 10
) -> WebElement:
    return WebDriverWait(navegador, timeout).until(
        EC.visibility_of_element_located((by, value))
    )


# -----------------------------------------------------------------------------
# Espera que um elemento web esteja clicável antes de retorná-lo
# -----------------------------------------------------------------------------


def espera_elemento_clicavel(
    navegador: WebDriver, by: str, value: str, timeout: int = 10
) -> WebElement:
    return WebDriverWait(navegador, timeout).until(
        EC.element_to_be_clickable((by, value))
    )


# -----------------------------------------------------------------------------
# Espera que um elemento web esteja presente na página antes de retorná-lo
# -----------------------------------------------------------------------------


def espera_presenca_elemento(
    navegador: WebDriver, by: str, value: str, timeout: int = 10
) -> WebElement:
    return WebDriverWait(navegador, timeout).until(
        EC.presence_of_element_located((by, value))
    )


# -----------------------------------------------------------------------------
# Clica em um botão a partir de um localizador
# -----------------------------------------------------------------------------


def clica_botao(navegador: WebDriver, by: str, value: str) -> None:

    botao = espera_elemento_clicavel(navegador, by, value)
    navegador.execute_script("arguments[0].scrollIntoView();", botao)
    navegador.execute_script("arguments[0].click();", botao)

    return None


# -----------------------------------------------------------------------------
# Insere texto em um elemento a partir de um localizador
# -----------------------------------------------------------------------------


def insere_texto(navegador: WebDriver, by: str, value: str, texto: str) -> None:

    caixa_texto = espera_presenca_elemento(navegador, by, value)
    caixa_texto.clear()
    caixa_texto.send_keys(texto)

    return None
