import time

from stealthbench.core.browser import BrowserHandle


class CreepJS:
    """Self-hosted CreepJS. Reports the LOCAL lie count only (trust score needs CreepJS's API)."""

    name = "creepjs"

    def __init__(self, base_url: str):
        self.url = base_url  # CreepJS serves at the root of its docs bundle

    def measure(self, handle: BrowserHandle) -> dict:
        handle.goto(self.url)
        for _ in range(45):
            time.sleep(1)
            ready = handle.evaluate(
                r'return /FP ID:\s*[0-9a-f]{16,}/i.test(document.body.innerText || "")'
            )
            if ready:
                time.sleep(3)  # let late lie rows render
                break
        lies = handle.evaluate("return document.querySelectorAll('.lies').length")
        return {"lies": int(lies)}
