from pathlib import Path

from stealthbench.core.results import (
    BenchResult,
    ConfigResult,
    DetectorResult,
    RunMetadata,
    Trial,
)
from stealthbench.history import load_series, tells_pct_series


def _cfg(name, passed, bot, lies):
    return ConfigResult(config=name, results=[
        DetectorResult(detector="tells", signals={"passed": passed, "total": 17}),
        DetectorResult(detector="botd", signals={"bot": bot, "kind": "selenium" if bot else ""}),
        DetectorResult(detector="creepjs", signals={"lies": lies}),
    ])


def _write(dir_: Path, filename, timestamp, schema_version, configs):
    bench = BenchResult(
        metadata=RunMetadata(
            schema_version=schema_version, timestamp=timestamp, browser="Chrome 149",
            os="Linux", headful=True, trials=1,
        ),
        trials=[Trial(configs=configs)],
    )
    (dir_ / filename).write_text(bench.to_json())


def test_load_series_sorts_by_timestamp_and_reads_v1_and_v2(tmp_path):
    # Written out of order; v2 file first, v1 file second — load must sort by timestamp.
    _write(tmp_path, "b.json", "2026-07-06T12:00:00+00:00", 2,
           [_cfg("vanilla", 14, True, 0), _cfg("camoufox", 16, False, 1)])
    _write(tmp_path, "a.json", "2026-07-05T09:00:00+00:00", 1,
           [_cfg("vanilla", 15, True, 0), _cfg("stealth", 16, True, 2)])

    series = load_series(tmp_path)

    assert [s.timestamp for s in series] == [
        "2026-07-05T09:00:00+00:00", "2026-07-06T12:00:00+00:00",
    ]
    assert [s.schema_version for s in series] == [1, 2]
    # metrics survive the round trip
    assert round(series[0].configs["vanilla"].tells_pct) == 88  # 15/17
    assert series[0].configs["vanilla"].botd_bot is True
    assert series[1].configs["camoufox"].creepjs_lies == 1


def test_absent_config_is_a_gap_never_fabricated(tmp_path):
    # Snapshot 1 has 3 configs; snapshot 2 drops "stealth" and adds "camoufox".
    _write(tmp_path, "a.json", "2026-07-05T09:00:00+00:00", 1,
           [_cfg("vanilla", 15, True, 0), _cfg("stealth", 16, True, 2),
            _cfg("uc", 16, False, 0)])
    _write(tmp_path, "b.json", "2026-07-06T12:00:00+00:00", 2,
           [_cfg("vanilla", 14, True, 0), _cfg("uc", 16, False, 0),
            _cfg("camoufox", 16, False, 1)])

    snapshots = load_series(tmp_path)
    series = tells_pct_series(snapshots)

    # stealth appears only in snapshot 1 -> None (gap) in snapshot 2, never forward-filled.
    assert series["stealth"][1] is None
    assert series["stealth"][0] is not None
    # camoufox appears only in snapshot 2 -> None in snapshot 1.
    assert series["camoufox"][0] is None
    assert series["camoufox"][1] is not None
    # every list is aligned to the snapshot count
    assert all(len(v) == len(snapshots) for v in series.values())


def test_missing_detector_is_a_gap(tmp_path):
    # A config whose tells detector errored: tells_pct is None, not a passing 0.
    errored = ConfigResult(config="c", results=[
        DetectorResult(detector="tells", signals={}, error="boom"),
    ])
    _write(tmp_path, "a.json", "2026-07-05T09:00:00+00:00", 2, [errored])
    snapshots = load_series(tmp_path)
    assert snapshots[0].configs["c"].tells_pct is None


def test_load_series_empty_dir_is_empty(tmp_path):
    assert load_series(tmp_path) == []
