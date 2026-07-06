from __future__ import annotations

from collections.abc import Callable
from typing import Any


def _wrap_script(script: str) -> str:
    """Translate a Selenium-style ``return <expr>`` script into a Playwright page
    function. Selenium's ``execute_script`` runs a statement body that may ``return``;
    Playwright's ``page.evaluate`` takes a JS expression or function instead, so the
    script is wrapped as a zero-arg arrow function.

    On Camoufox/Firefox (the only browser this handle drives), ``page.evaluate`` runs
    in the content world, where ``window`` is an *Xray wrapper*. Xray hides expando
    properties that page scripts set — so a detector page's ``window.__TELLS__`` /
    ``window.__BOTD__`` read back as ``undefined`` even though the DOM is shared. The
    page's real window is exposed at ``window.wrappedJSObject``, so the detector's
    ``window`` is rebound to it via an inner-function parameter (``|| window`` keeps
    the wrapper a no-op where ``wrappedJSObject`` is absent). Proven in the SBN-015
    spike; detectors keep their ``"return …"`` convention unchanged."""
    return f"() => {{ return (function (window) {{ {script} }})(window.wrappedJSObject || window); }}"


class PlaywrightHandle:
    """BrowserHandle over a Playwright Page. Lives under ``configs/`` — the only place a
    browser SDK is used. It never imports Playwright or Camoufox itself; it duck-types on
    the page object, so the translation logic is unit-testable with a fake page.

    ``on_quit`` tears down whatever built the page (e.g. the Camoufox context manager);
    the runner calls ``quit()`` in a ``finally``.
    """

    def __init__(self, page: Any, on_quit: Callable[[], None] | None = None):
        self._page = page
        self._on_quit = on_quit

    def goto(self, url: str) -> None:
        self._page.goto(url)

    def evaluate(self, script: str) -> Any:
        return self._page.evaluate(_wrap_script(script))

    def quit(self) -> None:
        if self._on_quit is not None:
            self._on_quit()
