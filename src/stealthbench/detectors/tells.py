from stealthbench.core.browser import BrowserHandle, wait_until


class TellsPanel:
    name = "tells"

    def __init__(self, base_url: str):
        self.url = f"{base_url}/tells.html"

    def measure(self, handle: BrowserHandle) -> dict:
        handle.goto(self.url)
        wait_until(handle, "return window.__TELLS__ !== undefined")
        return handle.evaluate("return window.__TELLS__")
