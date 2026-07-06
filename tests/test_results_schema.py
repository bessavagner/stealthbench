from stealthbench.core.results import (
    SCHEMA_VERSION,
    BenchResult,
    ConfigResult,
    DetectorResult,
    RunMetadata,
    Trial,
)


def _sample() -> BenchResult:
    return BenchResult(
        metadata=RunMetadata(
            timestamp="2026-07-06T10:00:00-03:00",
            browser="Chrome 149",
            os="Linux",
            headful=True,
            trials=1,
        ),
        trials=[
            Trial(
                configs=[
                    ConfigResult(
                        config="vanilla",
                        results=[
                            DetectorResult(detector="tells", signals={"passed": 15, "total": 17}),
                            DetectorResult(detector="botd", signals={"bot": True, "kind": "selenium"}),
                            DetectorResult(detector="creepjs", signals={"lies": 0}),
                        ],
                    )
                ]
            )
        ],
    )


def test_schema_version_defaults():
    assert _sample().metadata.schema_version == SCHEMA_VERSION == 1


def test_json_round_trip():
    original = _sample()
    restored = BenchResult.from_json(original.to_json())
    assert restored == original
    assert restored.trials[0].configs[0].results[0].signals["total"] == 17


def test_components_defaults_to_empty_for_v1():
    # A v1 metadata payload has no `components` key; it must still validate and default.
    meta = RunMetadata(
        timestamp="2026-07-06T10:00:00-03:00", browser="Chrome 149", os="Linux",
        headful=True, trials=1,
    )
    assert meta.components == {}


def test_components_round_trips():
    meta = RunMetadata(
        timestamp="2026-07-06T10:00:00-03:00", browser="Chrome 149", os="Linux",
        headful=True, trials=1, components={"chrome": "149", "selenium": "4.45.0"},
    )
    restored = RunMetadata.model_validate_json(meta.model_dump_json())
    assert restored.components == {"chrome": "149", "selenium": "4.45.0"}
