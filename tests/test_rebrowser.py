import pytest

from stealthbench.detectors.rebrowser import Rebrowser, _READY, _SCRAPE
from tests.conftest import FakeHandle


def test_rebrowser_reduces_to_test_counts_only():
    handle = FakeHandle({_READY: True, _SCRAPE: {"total": 10, "failed": 2}})
    det = Rebrowser("http://example.test")

    signals = det.measure(handle)

    assert signals == {"tests_total": 10, "tests_failed": 2}
    assert handle.visited == ["http://example.test/rebrowser.html"]


def test_rebrowser_malformed_payload_raises():
    handle = FakeHandle({_READY: True, _SCRAPE: "oops"})
    det = Rebrowser("http://example.test")

    with pytest.raises(RuntimeError, match="unusable signal"):
        det.measure(handle)


def test_rebrowser_empty_panel_raises_instead_of_a_false_pass():
    handle = FakeHandle({_READY: True, _SCRAPE: {"total": 0, "failed": 0}})
    det = Rebrowser("http://example.test")

    with pytest.raises(RuntimeError, match="no result rows"):
        det.measure(handle)
