from stealthbench.core.results import RunMetadata
from stealthbench.runner import run_bench
from tests.conftest import FakeConfig, FakeDetector, FakeHandle


def _meta(trials: int) -> RunMetadata:
    return RunMetadata(
        timestamp="2026-07-06T10:00:00-03:00",
        browser="fake",
        os="test",
        headful=False,
        trials=trials,
    )


def test_run_bench_shape_and_quit():
    handle = FakeHandle()
    cfg = FakeConfig("vanilla", handle)
    det = FakeDetector("tells", {"passed": 15, "total": 17})

    bench = run_bench([cfg], [det], _meta(trials=2))

    assert len(bench.trials) == 2
    first = bench.trials[0].configs[0]
    assert first.config == "vanilla"
    assert first.results[0].detector == "tells"
    assert first.results[0].signals == {"passed": 15, "total": 17}
    assert handle.quit_called is True


def test_detector_error_is_captured_not_raised():
    class Boom:
        name = "boom"

        def measure(self, handle):
            raise RuntimeError("detector exploded")

    bench = run_bench([FakeConfig("v", FakeHandle())], [Boom()], _meta(trials=1))
    dr = bench.trials[0].configs[0].results[0]
    assert dr.detector == "boom"
    assert dr.error is not None and "detector exploded" in dr.error
