from typing import Protocol, runtime_checkable

from stealthbench.core.browser import BrowserHandle


@runtime_checkable
class Detector(Protocol):
    """Measures normalized signals from a browser. Returns numbers only."""

    name: str

    def measure(self, handle: BrowserHandle) -> dict: ...
