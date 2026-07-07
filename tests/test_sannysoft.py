import pytest

from stealthbench.detectors.sannysoft import Sannysoft, _READY, _SCRAPE
from tests.conftest import FakeHandle


def test_sannysoft_reduces_rows_to_counts_only():
    handle = FakeHandle({_READY: True, _SCRAPE: {"passed": 16, "failed": 2, "total": 18}})
    det = Sannysoft("http://example.test")

    signals = det.measure(handle)

    assert signals == {"passed": 16, "failed": 2, "total": 18}
    assert handle.visited == ["http://example.test/sannysoft.html"]


def test_sannysoft_malformed_payload_raises_instead_of_a_zero():
    handle = FakeHandle({_READY: True, _SCRAPE: None})
    det = Sannysoft("http://example.test")

    with pytest.raises(RuntimeError, match="unusable signal"):
        det.measure(handle)


def test_sannysoft_empty_panel_raises_instead_of_a_false_pass():
    handle = FakeHandle({_READY: True, _SCRAPE: {"passed": 0, "failed": 0, "total": 0}})
    det = Sannysoft("http://example.test")

    with pytest.raises(RuntimeError, match="no result rows"):
        det.measure(handle)
