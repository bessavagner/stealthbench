from __future__ import annotations

from stealthbench.configs.playwright_handle import PlaywrightHandle


class CamoufoxConfig:
    """Camoufox (stealth Firefox) driven through Playwright's sync API.

    The Camoufox/Playwright SDK import is confined to ``build()``, so nothing outside
    ``configs/`` ever touches it. Camoufox spoofs the fingerprint by default and reports
    ``navigator.webdriver = false`` — those are its stealth defaults.
    """

    label = "camoufox"

    def build(self) -> PlaywrightHandle:
        from camoufox.sync_api import Camoufox  # lazy: SDK confined to configs/

        # headful (a headless browser is itself a strong tell); humanize adds
        # human-like cursor motion. Camoufox(...) is a context manager yielding a
        # Playwright Browser — enter it here and close it on quit(), since the runner
        # drives an explicit build()/quit() lifecycle rather than a `with` block.
        cam = Camoufox(headless=False, humanize=True)
        browser = cam.__enter__()
        page = browser.new_page()
        return PlaywrightHandle(page, on_quit=lambda: cam.__exit__(None, None, None))
