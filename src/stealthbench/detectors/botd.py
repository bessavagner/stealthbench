from stealthbench.core.browser import BrowserHandle, wait_until


class BotD:
    name = "botd"

    def __init__(self, base_url: str):
        self.url = f"{base_url}/botd.html"

    def measure(self, handle: BrowserHandle) -> dict:
        handle.goto(self.url)
        wait_until(handle, "return window.__BOTD__ !== undefined")
        raw = handle.evaluate("return window.__BOTD__")
        if not isinstance(raw, dict):
            raise RuntimeError(f"BotD returned an unusable signal: {raw!r}")
        if raw.get("error"):
            raise RuntimeError(f"BotD reported an error: {raw['error']}")
        result = raw.get("result")
        if not isinstance(result, dict):
            if "bot" not in raw:
                raise RuntimeError(f"BotD returned an unusable signal: {raw!r}")
            result = raw
        return {"bot": bool(result.get("bot")), "kind": result.get("botKind", "")}
