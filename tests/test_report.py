from stealthbench.core.results import (
    BenchResult,
    ConfigResult,
    DetectorResult,
    RunMetadata,
    Trial,
)
from stealthbench.history import ConfigMetrics, Snapshot
from stealthbench.report import _fmt_spread, _spread, _tells_pct_series, render_chart, render_trend, summarize


def _bench() -> BenchResult:
    def cfg(name, passed, bot, kind, lies):
        return ConfigResult(
            config=name,
            results=[
                DetectorResult(detector="tells", signals={"passed": passed, "total": 17}),
                DetectorResult(detector="botd", signals={"bot": bot, "kind": kind}),
                DetectorResult(detector="creepjs", signals={"lies": lies}),
            ],
        )

    meta = RunMetadata(
        timestamp="2026-07-06T10:00:00-03:00", browser="Chrome 149", os="Linux",
        headful=True, trials=1,
    )
    return BenchResult(
        metadata=meta,
        trials=[
            Trial(configs=[
                cfg("vanilla", 15, True, "selenium", 0),
                cfg("selenium-stealth", 16, True, "selenium", 2),
                cfg("undetected-chromedriver", 16, False, "", 0),
            ])
        ],
    )


def test_summarize_table_contents():
    md = summarize(_bench())
    assert "| Config |" in md
    assert "vanilla" in md and "caught (selenium)" in md
    assert "undetected-chromedriver" in md and "passed" in md
    # 15/17 -> 88, 16/17 -> 94
    assert "88" in md and "94" in md


def test_render_chart_writes_file(tmp_path):
    out = tmp_path / "pass-rate.png"
    render_chart(_bench(), str(out))
    assert out.exists() and out.stat().st_size > 0


def test_summarize_renders_na_for_missing_and_errored_detectors():
    meta = RunMetadata(
        timestamp="2026-07-06T10:00:00-03:00", browser="Chrome 149", os="Linux",
        headful=True, trials=1,
    )
    bench = BenchResult(
        metadata=meta,
        trials=[
            Trial(configs=[
                ConfigResult(
                    config="only-botd-errored",
                    results=[
                        # botd present but errored -> _signal() returns None -> "n/a"
                        DetectorResult(detector="botd", signals={}, error="boom"),
                        # tells + creepjs entirely absent -> "n/a"
                    ],
                )
            ])
        ],
    )

    md = summarize(bench)

    row = [ln for ln in md.splitlines() if ln.startswith("| only-botd-errored")][0]
    # tells %, BotD, CreepJS lies all render n/a
    assert row.count("n/a") == 3


# --- Group 1: spread helpers ---


def test_spread_multi_trial_reports_min_max_mean_stdev():
    sp = _spread([80.0, 90.0, 100.0])
    assert sp["min"] == 80.0
    assert sp["max"] == 100.0
    assert sp["mean"] == 90.0
    # population stdev of [80,90,100] = sqrt(200/3) ≈ 8.165
    assert round(sp["stdev"], 2) == 8.16


def test_spread_single_trial_has_zero_stdev():
    sp = _spread([88.0])
    assert sp == {"min": 88.0, "max": 88.0, "mean": 88.0, "stdev": 0.0}


def test_spread_empty_is_none():
    assert _spread([]) is None


def test_fmt_spread_renders_mean_stdev_range():
    assert _fmt_spread({"min": 82.0, "max": 94.0, "mean": 88.0, "stdev": 6.0}) == "88 ± 6 [82–94]"


def test_fmt_spread_none_is_na():
    assert _fmt_spread(None) == "n/a"


# --- Group 2: per-trial series ---


def test_tells_pct_series_collects_each_trial():
    bench = BenchResult(
        metadata=RunMetadata(
            timestamp="2026-07-06T10:00:00-03:00", browser="Chrome 149", os="Linux",
            headful=True, trials=3,
        ),
        trials=[
            Trial(configs=[ConfigResult(config="c", results=[
                DetectorResult(detector="tells", signals={"passed": 14, "total": 17})])]),
            Trial(configs=[ConfigResult(config="c", results=[
                DetectorResult(detector="tells", signals={"passed": 15, "total": 17})])]),
            Trial(configs=[ConfigResult(config="c", results=[
                DetectorResult(detector="tells", signals={"passed": 16, "total": 17})])]),
        ],
    )
    series = _tells_pct_series(bench, "c")
    assert [round(v) for v in series] == [82, 88, 94]


def test_tells_pct_series_excludes_errored_cell_not_counted_as_zero():
    bench = BenchResult(
        metadata=RunMetadata(
            timestamp="2026-07-06T10:00:00-03:00", browser="Chrome 149", os="Linux",
            headful=True, trials=2,
        ),
        trials=[
            Trial(configs=[ConfigResult(config="c", results=[
                DetectorResult(detector="tells", signals={"passed": 16, "total": 17})])]),
            # Errored detector: must be a gap, never a passing 0.
            Trial(configs=[ConfigResult(config="c", results=[
                DetectorResult(detector="tells", signals={}, error="boom")])]),
        ],
    )
    series = _tells_pct_series(bench, "c")
    assert len(series) == 1  # the errored trial is excluded, not appended as 0.0
    assert round(series[0]) == 94


# --- Group 3: reformatted summarize ---


def test_summarize_shows_spread_across_trials():
    meta = RunMetadata(
        timestamp="2026-07-06T10:00:00-03:00", browser="Chrome 149", os="Linux",
        headful=True, trials=3,
    )

    def cfg(passed):
        return ConfigResult(config="c", results=[
            DetectorResult(detector="tells", signals={"passed": passed, "total": 17}),
            DetectorResult(detector="botd", signals={"bot": False, "kind": ""}),
            DetectorResult(detector="creepjs", signals={"lies": 0}),
        ])

    bench = BenchResult(metadata=meta, trials=[
        Trial(configs=[cfg(14)]), Trial(configs=[cfg(15)]), Trial(configs=[cfg(16)]),
    ])
    md = summarize(bench)
    row = [ln for ln in md.splitlines() if ln.startswith("| c ")][0]
    # mean 88, range 82–94 for tells %; the ± and [–] spread markers are present.
    assert "88 ± " in row
    assert "[82–94]" in row


# --- Group 4: render_trend ---


def _snap(ts, configs):
    # configs: dict name -> tells_pct (float | None)
    return Snapshot(timestamp=ts, schema_version=2, configs={
        n: ConfigMetrics(tells_pct=p, botd_bot=False, creepjs_lies=0)
        for n, p in configs.items()
    })


def test_render_trend_multi_snapshot_writes_file(tmp_path):
    out = tmp_path / "trend.png"
    snaps = [
        _snap("2026-07-05T09:00:00+00:00", {"vanilla": 82.0, "camoufox": 90.0}),
        _snap("2026-07-06T12:00:00+00:00", {"vanilla": 88.0, "camoufox": 94.0}),
    ]
    render_trend(snaps, str(out))
    assert out.exists() and out.stat().st_size > 0


def test_render_trend_single_snapshot_writes_file(tmp_path):
    out = tmp_path / "trend.png"
    render_trend([_snap("2026-07-06T12:00:00+00:00", {"vanilla": 88.0})], str(out))
    assert out.exists() and out.stat().st_size > 0


def test_render_trend_with_config_gap_does_not_crash(tmp_path):
    out = tmp_path / "trend.png"
    snaps = [
        _snap("2026-07-05T09:00:00+00:00", {"vanilla": 82.0, "stealth": 90.0}),
        # camoufox appears only here; stealth dropped -> gap (None) for both series.
        _snap("2026-07-06T12:00:00+00:00", {"vanilla": 88.0, "camoufox": 94.0}),
    ]
    render_trend(snaps, str(out))
    assert out.exists() and out.stat().st_size > 0
