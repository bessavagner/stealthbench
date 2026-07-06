from __future__ import annotations

import argparse
import platform
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from stealthbench.configs.stealth import StealthConfig
from stealthbench.configs.uc import UcConfig
from stealthbench.configs.vanilla import VanillaConfig
from stealthbench.core.results import RunMetadata
from stealthbench.detectors.botd import BotD
from stealthbench.detectors.creepjs import CreepJS
from stealthbench.detectors.tells import TellsPanel
from stealthbench.report import render_chart, summarize
from stealthbench.runner import run_bench


def _chrome_major() -> int | None:
    for cmd in ("google-chrome", "google-chrome-stable", "chromium"):
        try:
            out = subprocess.check_output([cmd, "--version"], text=True)
            m = re.search(r"(\d+)\.", out)
            if m:
                return int(m.group(1))
        except (OSError, subprocess.SubprocessError):
            continue
    return None


def _stamp(timestamp: str) -> str:
    """Filesystem-safe, microsecond-precise stamp from an ISO-8601 timestamp.

    ``2026-07-06T15:52:31.123456+00:00`` -> ``20260706T155231123456``.
    Timezone offset is dropped; two runs in the same second differ by microseconds.
    """
    m = re.match(
        r"(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d+))?", timestamp
    )
    if m is None:
        raise ValueError(f"unparseable timestamp: {timestamp!r}")
    y, mo, d, h, mi, s, frac = m.groups()
    return f"{y}{mo}{d}T{h}{mi}{s}{frac or ''}"


def main() -> None:
    p = argparse.ArgumentParser(prog="stealthbench")
    p.add_argument("--trials", type=int, default=3)
    p.add_argument("--detector-host", default="http://localhost:8901")
    p.add_argument("--creep-host", default="http://localhost:8902")
    args = p.parse_args()

    chrome = _chrome_major()
    configs = [VanillaConfig(), StealthConfig(), UcConfig(chrome_major=chrome)]
    detectors = [
        TellsPanel(args.detector_host),
        BotD(args.detector_host),
        CreepJS(args.creep_host),
    ]
    meta = RunMetadata(
        timestamp=datetime.now(timezone.utc).isoformat(),
        browser=f"Chrome {chrome}" if chrome else "Chrome (unknown)",
        os=platform.platform(),
        headful=True,
        trials=args.trials,
    )

    bench = run_bench(configs, detectors, meta)

    out = Path("results")
    out.mkdir(exist_ok=True)
    stamp = _stamp(meta.timestamp)
    summary = summarize(bench)  # computed once, reused for file + print
    (out / f"{stamp}.json").write_text(bench.to_json())
    (out / "summary.md").write_text(summary)
    render_chart(bench, str(out / "pass-rate.png"))
    print(summary)
    print(f"\nwrote results/{stamp}.json + summary.md + pass-rate.png")


if __name__ == "__main__":
    main()
