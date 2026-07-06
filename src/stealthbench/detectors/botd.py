from stealthbench.core.browser import BrowserHandle, wait_until


class BotD:
    name = "botd"

    def __init__(self, base_url: str):
        self.url = f"{base_url}/botd.html"

    def measure(self, handle: BrowserHandle) -> dict:
        handle.goto(self.url)
        wait_until(handle, "return window.__BOTD__ !== undefined")
        raw = handle.evaluate("return window.__BOTD__")
        result = raw.get("result", raw) if isinstance(raw, dict) else {}
        return {"bot": bool(result.get("bot")), "kind": result.get("botKind", "")}
