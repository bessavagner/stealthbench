# spikes/015_camoufox_spike.py — THROWAWAY. Do not import from src/.
"""SBN-015 Camoufox transport + evaluate-translation spike (throwaway).

One-off manual validation. NOT part of the stealthbench package, never imported by
src/. Proves — before any production handle exists:

  1. SYNC DECISION: Camoufox drives from Python via its SYNC API
     (`camoufox.sync_api.Camoufox`). The BrowserHandle contract is sync, and this
     API is sync, so NO async bridge is needed. <<< sync-vs-async settled: SYNC.

  2. EVALUATE SHAPE (revised by the live spike): the detectors call
     evaluate("return <expr>") (Selenium's convention). Playwright's page.evaluate
     takes an expression/FUNCTION, not a statement body, so the script is wrapped as
     a zero-arg arrow function.

     BUT the plain `() => { <script> }` form is NOT enough on Camoufox/Firefox:
     Playwright's page.evaluate runs in Firefox's content world, where `window` is an
     XRAY WRAPPER. Xray hides expando properties that PAGE scripts set — so
     `window.__TELLS__` / `window.__BOTD__` (set by the detector pages' inline
     scripts) read back as `undefined`, even though document.title updates fine
     (the DOM is shared across worlds). Observed directly: title == "TELLS_DONE"
     while `typeof window.__TELLS__ === "undefined"`.

     Firefox exposes the page's REAL window at `window.wrappedJSObject`, where the
     expandos live. So the proven translation binds the detector script's `window`
     to that real window via an inner function parameter:

         () => { return (function (window) { <script> })(window.wrappedJSObject || window); }

     `window.wrappedJSObject` is Firefox-only; `|| window` keeps the wrapper a no-op
     anywhere it's absent. This is the exact translation PlaywrightHandle implements
     in SBN-016 (and its tests assert this string, not the plain arrow form).

  3. Camoufox reads the LOCAL detector pages (self-hosted invariant) and their
     window globals (__TELLS__, __BOTD__) populate and are readable through the
     wrappedJSObject wrapper. Observed: TELLS passed 14/17; BOTD {'bot': False}.

Prereqs (see README):
  uv sync                # installs camoufox + playwright (pinned <1.60)
  uv run camoufox fetch  # downloads the patched Firefox once
  # tells + BotD server on :8901:
  ( cd src/stealthbench/detectors/assets && npm ci && python3 -m http.server 8901 ) &

Run headful:
  uv run python spikes/015_camoufox_spike.py

API confirmed via context7 (/daijro/camoufox): `from camoufox.sync_api import Camoufox`
is a context manager yielding a Playwright Browser; browser.new_page() -> Page;
page.goto / page.evaluate are unmodified Playwright sync-API calls. `humanize=True`
is a valid launch kwarg (Optional[Union[bool, float]]).
"""
import time

from camoufox.sync_api import Camoufox

HOST = "http://localhost:8901"


def _wrap(script: str) -> str:
    # EXACT translation PlaywrightHandle will implement: wrap the detector's
    # `return <expr>` as an arrow function, and bind `window` to the page's real
    # window (Firefox's wrappedJSObject) so page-set expandos resolve past the Xray.
    return f"() => {{ return (function (window) {{ {script} }})(window.wrappedJSObject || window); }}"


def read_global(page, name: str):
    return page.evaluate(_wrap(f"return window.{name}"))


def wait_for_global(page, name: str, timeout: float = 25.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if page.evaluate(_wrap(f"return window.{name} !== undefined")):
            return
        time.sleep(0.5)
    raise TimeoutError(f"window.{name} never defined")


def main() -> None:
    with Camoufox(headless=False) as browser:
        page = browser.new_page()

        page.goto(f"{HOST}/tells.html")
        wait_for_global(page, "__TELLS__")
        print("TELLS:", read_global(page, "__TELLS__"))

        page.goto(f"{HOST}/botd.html")
        wait_for_global(page, "__BOTD__")
        print("BOTD:", read_global(page, "__BOTD__"))


if __name__ == "__main__":
    main()
