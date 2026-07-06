from __future__ import annotations

import statistics

from stealthbench.core.results import BenchResult


def _signal(config, detector: str) -> dict | None:
    for r in config.results:
        if r.detector == detector and r.error is None:
            return r.signals
    return None


def _config_names(bench: BenchResult) -> list[str]:
    return [c.config for c in bench.trials[0].configs] if bench.trials else []


def _spread(values: list[float]) -> dict | None:
    """Descriptive spread of a small sample of per-trial values.

    Reports min/max/mean and **population** stdev — descriptive spread over small N,
    never an inferential confidence interval. A single value yields stdev ``0.0``; an
    empty list yields ``None`` (rendered ``"n/a"``).
    """
    if not values:
        return None
    return {
        "min": min(values),
        "max": max(values),
        "mean": statistics.fmean(values),
        "stdev": statistics.pstdev(values),
    }


def _fmt_spread(sp: dict | None) -> str:
    if sp is None:
        return "n/a"
    m, sd = round(sp["mean"]), round(sp["stdev"])
    lo, hi = round(sp["min"]), round(sp["max"])
    return f"{m} ± {sd} [{lo}–{hi}]"


def _tells_pct_series(bench: BenchResult, name: str) -> list[float]:
    vals: list[float] = []
    for trial in bench.trials:
        for c in trial.configs:
            if c.config == name:
                s = _signal(c, "tells")
                if s and s.get("total"):
                    vals.append(100 * s["passed"] / s["total"])
    return vals


def _avg_tells_pct(bench: BenchResult, name: str) -> float | None:
    vals = _tells_pct_series(bench, name)
    return sum(vals) / len(vals) if vals else None


def _lies_series(bench: BenchResult, name: str) -> list[int]:
    vals: list[int] = []
    for trial in bench.trials:
        for c in trial.configs:
            if c.config == name:
                s = _signal(c, "creepjs")
                if s is not None and "lies" in s:
                    vals.append(s["lies"])
    return vals


def _last(bench: BenchResult, name: str, detector: str) -> dict | None:
    found = None
    for trial in bench.trials:
        for c in trial.configs:
            if c.config == name:
                s = _signal(c, detector)
                if s is not None:
                    found = s
    return found


def _botd_label(signals: dict | None) -> str:
    if signals is None:
        return "n/a"
    if not signals.get("bot"):
        return "passed"
    kind = signals.get("kind") or "bot"
    return f"caught ({kind})"


def summarize(bench: BenchResult) -> str:
    lines = ["| Config | Tells % | BotD | CreepJS lies |", "|---|---|---|---|"]
    for name in _config_names(bench):
        tells = _fmt_spread(_spread(_tells_pct_series(bench, name)))
        botd = _botd_label(_last(bench, name, "botd"))
        lies = _fmt_spread(_spread([float(v) for v in _lies_series(bench, name)]))
        lines.append(f"| {name} | {tells} | {botd} | {lies} |")
    return "\n".join(lines)


def render_chart(bench: BenchResult, out_path: str) -> None:
    from stealthbench import _style

    _style.apply()
    import matplotlib.pyplot as plt

    names = _config_names(bench)
    pcts = [(_avg_tells_pct(bench, n) or 0) for n in names]
    colors = [
        _style.PALETTE["passed"]
        if not (_last(bench, n, "botd") or {}).get("bot")
        else _style.PALETTE["caught"]
        for n in names
    ]
    fig, ax = plt.subplots(figsize=(7.4, 4.6))
    bars = ax.bar(range(len(names)), pcts, color=colors, width=0.6)
    ax.set_ylim(0, 100)
    ax.set_ylabel("Automation-tells passed (%)")
    ax.set_title("stealthbench — tells panel (bar colour = BotD verdict)")
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, rotation=10, ha="right")
    ax.bar_label(bars, fmt="%.0f%%", padding=3)
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)
