from stealthbench.core.results import (
    BenchResult,
    ConfigResult,
    DetectorResult,
    RunMetadata,
    Trial,
)
from stealthbench.report import render_chart, summarize


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
