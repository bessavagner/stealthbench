from selenium import webdriver

from stealthbench.configs.selenium_handle import SeleniumHandle
from stealthbench.configs.vanilla import _base_options


class StealthConfig:
    label = "selenium-stealth"

    def build(self) -> SeleniumHandle:
        o = _base_options()
        o.add_argument("--disable-blink-features=AutomationControlled")
        o.add_experimental_option("excludeSwitches", ["enable-automation"])
        driver = webdriver.Chrome(options=o)
        from selenium_stealth import stealth

        stealth(driver, languages=["en-US", "en"], vendor="Google Inc.",
                platform="Win32", webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine", fix_hairline=True)
        return SeleniumHandle(driver)
