import pytest

from stealthbench.core.browser import BrowserHandle, wait_until
from stealthbench.core.config import Config
from stealthbench.core.detector import Detector


def test_fakes_satisfy_protocols(fake_handle):
    from tests.conftest import FakeConfig, FakeDetector

    assert isinstance(fake_handle, BrowserHandle)
    assert isinstance(FakeConfig("v", fake_handle), Config)
    assert isinstance(FakeDetector("d", {}), Detector)


def test_wait_until_returns_when_truthy():
    class H:
        def __init__(self):
            self.calls = 0

        def goto(self, url): ...
        def quit(self): ...

        def evaluate(self, script):
            self.calls += 1
            return self.calls >= 2  # falsy first, truthy second

    h = H()
    wait_until(h, "ready", timeout=5, interval=0.01)
    assert h.calls == 2


def test_wait_until_times_out():
    class H:
        def goto(self, url): ...
        def quit(self): ...
        def evaluate(self, script):
            return False

    with pytest.raises(TimeoutError):
        wait_until(H(), "never", timeout=0.05, interval=0.01)
