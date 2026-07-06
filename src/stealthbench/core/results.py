from __future__ import annotations

from pydantic import BaseModel

SCHEMA_VERSION = 1


class RunMetadata(BaseModel):
    schema_version: int = SCHEMA_VERSION
    timestamp: str
    browser: str
    os: str
    headful: bool
    trials: int
    single_ip_caveat: bool = True
    components: dict[str, str] = {}


class DetectorResult(BaseModel):
    detector: str
    signals: dict = {}
    error: str | None = None


class ConfigResult(BaseModel):
    config: str
    results: list[DetectorResult] = []
    error: str | None = None


class Trial(BaseModel):
    configs: list[ConfigResult] = []


class BenchResult(BaseModel):
    metadata: RunMetadata
    trials: list[Trial] = []

    def to_json(self) -> str:
        return self.model_dump_json(indent=2)

    @classmethod
    def from_json(cls, raw: str) -> "BenchResult":
        return cls.model_validate_json(raw)
