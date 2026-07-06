import importlib.metadata

from stealthbench.env import _DRIVER_PACKAGES, capture_components


def test_capture_records_chrome_major_as_string():
    comps = capture_components(chrome_major=149)
    assert comps["chrome"] == "149"


def test_capture_marks_unknown_chrome_when_missing():
    comps = capture_components(chrome_major=None)
    assert comps["chrome"] == "unknown"


def test_capture_reads_installed_driver_versions():
    comps = capture_components(chrome_major=149)
    # selenium is a hard dependency, so its real version is present (not "unknown").
    assert comps["selenium"] != "unknown"
    assert all(pkg in comps for pkg in _DRIVER_PACKAGES)


def test_capture_degrades_to_unknown_on_metadata_failure(monkeypatch):
    def boom(_name):
        raise importlib.metadata.PackageNotFoundError

    monkeypatch.setattr(importlib.metadata, "version", boom)
    comps = capture_components(chrome_major=149)
    # Every driver lookup failed but the call did not crash; chrome still captured.
    assert comps["chrome"] == "149"
    assert all(comps[pkg] == "unknown" for pkg in _DRIVER_PACKAGES)


def test_capture_is_numbers_only():
    # Numbers-only invariant: keys are limited to chrome + the driver packages.
    comps = capture_components(chrome_major=149)
    assert set(comps) == {"chrome", *_DRIVER_PACKAGES}
