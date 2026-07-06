import pytest

from stealthbench.detectors.botd import BotD
from stealthbench.detectors.creepjs import CreepJS
from tests.conftest import FakeHandle


def test_botd_success_bot_detected():
    handle = FakeHandle(
        {
            "return window.__BOTD__ !== undefined": True,
            "return window.__BOTD__": {"result": {"bot": True, "botKind": "selenium"}},
        }
    )
    det = BotD("http://example.test")

    signals = det.measure(handle)

    assert signals == {"bot": True, "kind": "selenium"}


def test_botd_success_not_a_bot():
    handle = FakeHandle(
        {
            "return window.__BOTD__ !== undefined": True,
            "return window.__BOTD__": {"result": {"bot": False}},
        }
    )
    det = BotD("http://example.test")

    signals = det.measure(handle)

    assert signals == {"bot": False, "kind": ""}


def test_botd_error_raises_instead_of_false_pass():
    handle = FakeHandle(
        {
            "return window.__BOTD__ !== undefined": True,
            "return window.__BOTD__": {"error": "load failed"},
        }
    )
    det = BotD("http://example.test")

    with pytest.raises(RuntimeError, match="load failed"):
        det.measure(handle)


def test_creepjs_timeout_raises_instead_of_reading_partial_dom(monkeypatch):
    handle = FakeHandle(
        {
            r'return /FP ID:\s*[0-9a-f]{16,}/i.test(document.body.innerText || "")': False,
            "return document.querySelectorAll('.lies').length": 0,
        }
    )
    monkeypatch.setattr("stealthbench.detectors.creepjs.time.sleep", lambda *_: None)
    det = CreepJS("http://example.test")

    with pytest.raises(TimeoutError):
        det.measure(handle)
