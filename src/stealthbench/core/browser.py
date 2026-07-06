import time
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class BrowserHandle(Protocol):
    """Driver-agnostic browser control. `evaluate` runs JS that must `return`."""

    def goto(self, url: str) -> None: ...
    def evaluate(self, script: str) -> Any: ...
    def quit(self) -> None: ...


def wait_until(
    handle: BrowserHandle, script: str, timeout: float = 25.0, interval: float = 0.5
) -> None:
    """Poll handle.evaluate(script) until truthy, or raise TimeoutError."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if handle.evaluate(script):
            return
        time.sleep(interval)
    raise TimeoutError(f"condition never became truthy: {script!r}")
