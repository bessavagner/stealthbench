from __future__ import annotations

import argparse
import platform
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from stealthbench.configs.camoufox import CamoufoxConfig
from stealthbench.configs.nodriver import NodriverConfig
from stealthbench.configs.stealth import StealthConfig
from stealthbench.configs.uc import UcConfig
from stealthbench.configs.vanilla import VanillaConfig
from stealthbench.core.results import RunMetadata
from stealthbench.env import capture_components
from stealthbench.detectors.botd import BotD
from stealthbench.detectors.creepjs import CreepJS
from stealthbench.detectors.rebrowser import Rebrowser
from stealthbench.detectors.sannysoft import Sannysoft
from stealthbench.detectors.tells import TellsPanel
from stealthbench.history import load_series
from stealthbench.report import render_chart, render_trend, summarize
from stealthbench.runner import run_bench
from stealthbench.selection import (
    CONFIG_NAMES,
    DETECTOR_NAMES,
    filter_configs,
    filter_detectors,
    parse_selection,
)


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
    p.add_argument(
        "--config",
        action="append",
        metavar="NAME",
        help="config to run (repeatable, comma-ok); default: all. "
        "one of: " + ", ".join(CONFIG_NAMES),
    )
    p.add_argument(
        "--detector",
        action="append",
        metavar="NAME",
        help="detector to run (repeatable, comma-ok); default: all. "
        "one of: " + ", ".join(DETECTOR_NAMES),
    )
    args = p.parse_args()

    try:
        config_names = parse_selection(args.config, CONFIG_NAMES, "config")
        detector_names = parse_selection(args.detector, DETECTOR_NAMES, "detector")
    except ValueError as exc:
        p.error(str(exc))  # exit 2 at parse time; never a silent empty run

    chrome = _chrome_major()
    configs = filter_configs(
        [
            VanillaConfig(),
            StealthConfig(),
            UcConfig(chrome_major=chrome),
            CamoufoxConfig(),
            NodriverConfig(),
        ],
        config_names,
    )
    detectors = filter_detectors(
        [
            TellsPanel(args.detector_host),
            BotD(args.detector_host),
            Sannysoft(args.detector_host),
            Rebrowser(args.detector_host),
            CreepJS(args.creep_host),
        ],
        detector_names,
    )
    meta = RunMetadata(
        timestamp=datetime.now(timezone.utc).isoformat(),
        browser=(f"Chrome {chrome}" if chrome else "Chrome (unknown)") + " + Camoufox",
        os=platform.platform(),
        headful=True,
        trials=args.trials,
        components=capture_components(chrome),
    )

    bench = run_bench(configs, detectors, meta)

    out = Path("results")
    out.mkdir(exist_ok=True)
    stamp = _stamp(meta.timestamp)
    summary = summarize(bench)  # computed once, reused for file + print
    (out / f"{stamp}.json").write_text(bench.to_json())
    (out / "summary.md").write_text(summary)
    render_chart(bench, str(out / "pass-rate.png"))
    render_trend(load_series(out), str(out / "trend.png"))
    print(summary)
    print(f"\nwrote results/{stamp}.json + summary.md + pass-rate.png + trend.png")


if __name__ == "__main__":
    main()
