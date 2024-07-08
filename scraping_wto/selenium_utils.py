import subprocess
from pathlib import Path

import requests
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as GeckoService
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from scraping_wto.utils import get_path_projeto


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
        print(f"{path_download} já existe!")
        return None

    with open(path_download, "wb") as download_f:
        response = requests.get(url_download)
        download_f.write(response.content)

    return None


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
    firefox_options.set_preference(
        "browser.download.manager.showWhenStarting", False
    )
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


def espera_elemento_clicavel(
    navegador: WebDriver, by: str, value: str
) -> None:
    # Bibliotecas

    # Esperando
    wait = WebDriverWait(navegador, 10)
    wait.until(EC.element_to_be_clickable((by, value)))

    return None


def espera_elemento_visivel(navegador: WebDriver, by: str, value: str) -> None:
    # Bibliotecas

    # Esperando
    wait = WebDriverWait(navegador, 10)
    wait.until(EC.visibility_of_element_located((by, value)))

    return None


def clica_botao(navegador: WebDriver, by: str, value: str) -> None:
    # Clicando
    espera_elemento_clicavel(navegador, by, value)
    botao = navegador.find_element(by, value)
    navegador.execute_script("arguments[0].scrollIntoView();", botao)
    navegador.execute_script("arguments[0].click();", botao)

    return None
