from stealthbench.core.browser import BrowserHandle, wait_until

_READY = "return window.__SANNYSOFT_DONE__ === true"

_SCRAPE = """return (function () {
  const rows = Array.from(document.querySelectorAll('table#results tr.check'));
  let passed = 0, failed = 0;
  for (const r of rows) {
    if (r.classList.contains('passed')) passed++;
    else if (r.classList.contains('failed')) failed++;
  }
  return { passed: passed, failed: failed, total: passed + failed };
})()"""


class Sannysoft:
    name = "sannysoft"

    def __init__(self, base_url: str):
        self.url = f"{base_url}/sannysoft.html"

    def measure(self, handle: BrowserHandle) -> dict:
        handle.goto(self.url)
        wait_until(handle, _READY)
        raw = handle.evaluate(_SCRAPE)
        if not isinstance(raw, dict) or "total" not in raw:
            raise RuntimeError(f"sannysoft returned an unusable signal: {raw!r}")
        total = int(raw["total"])
        if total <= 0:
            raise RuntimeError("sannysoft panel rendered no result rows")
        return {"passed": int(raw["passed"]), "failed": int(raw["failed"]), "total": total}
