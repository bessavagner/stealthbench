import pytest

from stealthbench.selection import (
    CONFIG_NAMES,
    DETECTOR_NAMES,
    filter_configs,
    filter_detectors,
    parse_selection,
)
from tests.conftest import FakeConfig, FakeDetector, FakeHandle


def _configs():
    # canonical order mirrors __main__: vanilla, selenium-stealth, undetected-chromedriver,
    # camoufox, nodriver
    return [FakeConfig(label, FakeHandle()) for label in CONFIG_NAMES.values()]


def _detectors():
    return [FakeDetector(name, {}) for name in DETECTOR_NAMES]


def test_parse_selection_none_when_no_values():
    assert parse_selection(None, CONFIG_NAMES, "config") is None
    assert parse_selection([], CONFIG_NAMES, "config") is None


def test_parse_selection_splits_commas_and_repeats():
    # argparse append gives a list; each item may itself be comma-joined
    assert parse_selection(["vanilla,uc", "nodriver"], CONFIG_NAMES, "config") == [
        "vanilla",
        "uc",
        "nodriver",
    ]


def test_parse_selection_dedupes_preserving_first_seen_order():
    assert parse_selection(["uc", "vanilla", "uc"], CONFIG_NAMES, "config") == [
        "uc",
        "vanilla",
    ]


def test_parse_selection_unknown_raises_listing_valid_names():
    with pytest.raises(ValueError) as exc:
        parse_selection(["bogus"], CONFIG_NAMES, "config")
    msg = str(exc.value)
    assert "bogus" in msg
    assert "vanilla" in msg and "nodriver" in msg  # valid list is shown


def test_parse_selection_unknown_detector_raises():
    with pytest.raises(ValueError):
        parse_selection(["nope"], DETECTOR_NAMES, "detector")


def test_filter_configs_none_is_identity():
    configs = _configs()
    assert filter_configs(configs, None) is configs  # bare run == today's matrix


def test_filter_configs_selects_subset_in_canonical_order():
    configs = _configs()
    # request out of order; result must keep canonical (input) order
    got = filter_configs(configs, ["uc", "vanilla"])
    assert [c.label for c in got] == ["vanilla", "undetected-chromedriver"]


def test_filter_detectors_none_is_identity():
    detectors = _detectors()
    assert filter_detectors(detectors, None) is detectors


def test_filter_detectors_selects_subset_in_canonical_order():
    detectors = _detectors()
    got = filter_detectors(detectors, ["creepjs", "tells"])
    assert [d.name for d in got] == ["tells", "creepjs"]
