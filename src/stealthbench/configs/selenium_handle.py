from __future__ import annotations

from typing import Any

from selenium.webdriver.remote.webdriver import WebDriver


class SeleniumHandle:
    """BrowserHandle over a Selenium WebDriver. `evaluate` runs JS that must `return`."""

    def __init__(self, driver: WebDriver):
        self._driver = driver

    def goto(self, url: str) -> None:
        self._driver.get(url)

    def evaluate(self, script: str) -> Any:
        return self._driver.execute_script(script)

    def quit(self) -> None:
        self._driver.quit()
