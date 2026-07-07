from __future__ import annotations

from stealthbench.configs.nodriver_handle import NodriverHandle


class NodriverConfig:
    """nodriver — the direct-CDP successor to undetected-chromedriver, a third driver family
    beyond selenium and Playwright/Camoufox.

    The nodriver SDK import is confined to ``build()`` (lazy, mirroring ``CamoufoxConfig`` /
    ``uc.py``), so nothing outside ``configs/`` touches it. The private asyncio loop that drives
    nodriver's async API is owned here and torn down in ``on_quit``.
    """

    label = "nodriver"

    def build(self) -> NodriverHandle:
        import asyncio

        import nodriver as uc  # lazy: SDK confined to configs/

        # headful by design (a headless browser is itself a strong tell).
        loop = asyncio.new_event_loop()
        browser = loop.run_until_complete(uc.start(headless=False))
        tab = loop.run_until_complete(browser.get("about:blank"))

        def _quit() -> None:
            try:
                browser.stop()  # confirmed synchronous in nodriver
            except Exception:
                pass
            finally:
                loop.close()

        return NodriverHandle(tab, loop, on_quit=_quit)
