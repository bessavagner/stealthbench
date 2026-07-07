from stealthbench.core.browser import BrowserHandle, wait_until

_READY = "return window.__REBROWSER_DONE__ === true"

_SCRAPE = """return (function () {
  const ds = Array.isArray(window.detections) ? window.detections : [];
  let total = ds.length, failed = 0;
  for (const d of ds) {
    if (d.rating >= 1) failed++;
  }
  return { total: total, failed: failed };
})()"""


class Rebrowser:
    name = "rebrowser"

    def __init__(self, base_url: str):
        self.url = f"{base_url}/rebrowser.html"

    def measure(self, handle: BrowserHandle) -> dict:
        handle.goto(self.url)
        wait_until(handle, _READY)
        raw = handle.evaluate(_SCRAPE)
        if not isinstance(raw, dict) or "total" not in raw:
            raise RuntimeError(f"rebrowser returned an unusable signal: {raw!r}")
        total = int(raw["total"])
        if total <= 0:
            raise RuntimeError("rebrowser panel rendered no result rows")
        return {"tests_total": total, "tests_failed": int(raw.get("failed", 0))}
