from typing import Any

import pytest

from stealthbench.core.browser import BrowserHandle
from stealthbench.core.config import Config  # noqa: F401
from stealthbench.core.detector import Detector  # noqa: F401


class FakeHandle:
    """A scripted BrowserHandle: evaluate() pops canned return values by call order."""

    def __init__(self, returns: dict[str, Any] | None = None):
        self.returns = returns or {}
        self.visited: list[str] = []
        self.quit_called = False

    def goto(self, url: str) -> None:
        self.visited.append(url)

    def evaluate(self, script: str) -> Any:
        return self.returns.get(script)

    def quit(self) -> None:
        self.quit_called = True


class FakeConfig:
    def __init__(self, label: str, handle: FakeHandle):
        self.label = label
        self._handle = handle

    def build(self) -> BrowserHandle:
        return self._handle


class FakeDetector:
    def __init__(self, name: str, signals: dict):
        self.name = name
        self._signals = signals

    def measure(self, handle: BrowserHandle) -> dict:
        return dict(self._signals)


@pytest.fixture
def fake_handle() -> FakeHandle:
    return FakeHandle()
