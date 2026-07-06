from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from stealthbench.core.results import BenchResult
from stealthbench.report import _avg_tells_pct, _config_names, _last


@dataclass(frozen=True)
class ConfigMetrics:
    tells_pct: float | None
    botd_bot: bool | None
    creepjs_lies: int | None


@dataclass(frozen=True)
class Snapshot:
    timestamp: str
    schema_version: int
    configs: dict[str, ConfigMetrics]


def _config_metrics(bench: BenchResult, name: str) -> ConfigMetrics:
    botd = _last(bench, name, "botd")
    creep = _last(bench, name, "creepjs")
    return ConfigMetrics(
        tells_pct=_avg_tells_pct(bench, name),
        botd_bot=(botd.get("bot") if botd is not None else None),
        creepjs_lies=(creep["lies"] if creep is not None and "lies" in creep else None),
    )


def load_series(results_dir: str | Path) -> list[Snapshot]:
    """Aggregate every ``results/*.json`` snapshot into a timestamp-sorted series.

    Pure: no browser, no network. Each file is validated via ``BenchResult.from_json``
    (tolerating both v1 and v2). A config absent from a snapshot is simply not a key in
    that snapshot's ``configs`` map — callers treat the gap as ``None``, never fabricate
    or forward-fill it. Missing/errored detectors surface as ``None`` metric values.

    Reuses ``report``'s metric helpers, so the series can never disagree with the table.
    """
    snapshots: list[Snapshot] = []
    for path in sorted(Path(results_dir).glob("*.json")):
        bench = BenchResult.from_json(path.read_text())
        configs = {n: _config_metrics(bench, n) for n in _config_names(bench)}
        snapshots.append(
            Snapshot(
                timestamp=bench.metadata.timestamp,
                schema_version=bench.metadata.schema_version,
                configs=configs,
            )
        )
    snapshots.sort(key=lambda s: s.timestamp)
    return snapshots


def tells_pct_series(snapshots: list[Snapshot]) -> dict[str, list[float | None]]:
    """Pivot into per-config tells-% across snapshots, ``None`` where a config is absent.

    Every config seen in ANY snapshot gets a list aligned with ``snapshots`` order; a
    snapshot lacking that config contributes ``None`` (a gap, never forward-filled).
    """
    names: list[str] = []
    for snap in snapshots:
        for n in snap.configs:
            if n not in names:
                names.append(n)
    series: dict[str, list[float | None]] = {n: [] for n in names}
    for snap in snapshots:
        for n in names:
            metrics = snap.configs.get(n)
            series[n].append(metrics.tells_pct if metrics is not None else None)
    return series
