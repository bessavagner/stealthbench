from __future__ import annotations

from stealthbench.core.config import Config
from stealthbench.core.detector import Detector
from stealthbench.core.results import (
    BenchResult,
    ConfigResult,
    DetectorResult,
    RunMetadata,
    Trial,
)


def _describe(exc: Exception) -> str:
    return f"{type(exc).__name__}: {exc}"


def run_bench(
    configs: list[Config], detectors: list[Detector], metadata: RunMetadata
) -> BenchResult:
    trials: list[Trial] = []
    for _ in range(metadata.trials):
        config_results: list[ConfigResult] = []
        for cfg in configs:
            handle = None
            try:
                handle = cfg.build()
                det_results: list[DetectorResult] = []
                for det in detectors:
                    try:
                        det_results.append(
                            DetectorResult(detector=det.name, signals=det.measure(handle))
                        )
                    except Exception as exc:  # a bad detector must not kill the run
                        det_results.append(
                            DetectorResult(detector=det.name, signals={}, error=_describe(exc))
                        )
                config_results.append(ConfigResult(config=cfg.label, results=det_results))
            except Exception as exc:  # a config that won't build is recorded, not fatal
                config_results.append(ConfigResult(config=cfg.label, error=_describe(exc)))
            finally:
                if handle is not None:
                    try:
                        handle.quit()
                    except Exception:
                        pass
        trials.append(Trial(configs=config_results))
    return BenchResult(metadata=metadata, trials=trials)
