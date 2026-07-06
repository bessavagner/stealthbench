from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from stealthbench.configs.selenium_handle import SeleniumHandle


def _base_options() -> Options:
    o = Options()
    o.add_argument("--no-sandbox")
    o.add_argument("--disable-dev-shm-usage")
    o.add_argument("--window-size=1280,900")
    return o


class VanillaConfig:
    label = "vanilla"

    def build(self) -> SeleniumHandle:
        return SeleniumHandle(webdriver.Chrome(options=_base_options()))
