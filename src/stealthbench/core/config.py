from typing import Protocol, runtime_checkable

from stealthbench.core.browser import BrowserHandle


@runtime_checkable
class Config(Protocol):
    """An adapter that builds a fresh BrowserHandle for one stealth setup."""

    label: str

    def build(self) -> BrowserHandle: ...
