from __future__ import annotations

import importlib.metadata

# Driver packages whose versions attribute a number to a specific stack.
# Numbers-only: these are package version strings — no IP, fingerprint, or account data.
_DRIVER_PACKAGES = (
    "selenium",
    "selenium-stealth",
    "undetected-chromedriver",
    "playwright",
    "camoufox",
)


def capture_components(chrome_major: int | None = None) -> dict[str, str]:
    """Capture the browser + driver versions exercised by a run.

    Values are read from the environment at run time (never hand-typed); each lookup
    degrades to ``"unknown"`` on failure rather than aborting the run — mirroring
    ``__main__._chrome_major``'s defensive pattern. Numbers-only: only a browser major
    and package version strings are recorded, never IP/fingerprint/account data.

    Reading ``importlib.metadata.version("camoufox")`` uses a string literal, not an
    SDK import, so it does not touch the provider seam.
    """
    components: dict[str, str] = {
        "chrome": str(chrome_major) if chrome_major is not None else "unknown",
    }
    for pkg in _DRIVER_PACKAGES:
        try:
            components[pkg] = importlib.metadata.version(pkg)
        except Exception:  # PackageNotFoundError or any metadata read failure
            components[pkg] = "unknown"
    return components
