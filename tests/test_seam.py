import re
from pathlib import Path

# Matches a top-level SDK import: `import camoufox`, `import playwright`, `import nodriver`,
# `from camoufox.X`, `from playwright.X`, `from nodriver.X`. Does NOT match
# `from stealthbench.configs.camoufox import CamoufoxConfig` (that's `from stealthbench…`).
_SDK_IMPORT = re.compile(
    r"(?m)^\s*(?:import\s+(?:camoufox|playwright|nodriver)"
    r"|from\s+(?:camoufox|playwright|nodriver)[.\s])"
)

_SRC = Path(__file__).resolve().parent.parent / "src" / "stealthbench"


def test_no_browser_sdk_import_outside_configs():
    offenders = []
    for path in _SRC.rglob("*.py"):
        if "configs" in path.parts:
            continue  # configs/ is the ONLY place a browser SDK may be imported
        if _SDK_IMPORT.search(path.read_text()):
            offenders.append(str(path.relative_to(_SRC)))
    assert offenders == [], f"browser SDK imported outside configs/: {offenders}"
