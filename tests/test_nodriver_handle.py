import asyncio
import json

from stealthbench.configs.nodriver_handle import NodriverHandle, _wrap_script


class FakeTab:
    """Duck-typed nodriver tab: async get/evaluate. Like real nodriver, ``evaluate`` returns
    the value of the JSON.stringify'd expression — i.e. a JSON *string* — canned by expression.
    """

    def __init__(self, returns=None):
        self.returns = returns or {}
        self.visited = []

    async def get(self, url):
        self.visited.append(url)

    async def evaluate(self, expr, await_promise=False, return_by_value=True):
        return self.returns.get(expr)


def test_wrap_script_json_stringifies_an_iife_expression():
    assert (
        _wrap_script("return window.__BOTD__")
        == "JSON.stringify((() => { return window.__BOTD__ })())"
    )


def test_goto_and_evaluate_drive_the_async_tab_and_json_decode_the_result():
    loop = asyncio.new_event_loop()
    try:
        expr = _wrap_script("return {passed: 16, total: 18}")
        tab = FakeTab({expr: json.dumps({"passed": 16, "total": 18})})
        handle = NodriverHandle(tab, loop)

        handle.goto("http://example.test")
        result = handle.evaluate("return {passed: 16, total: 18}")

        assert tab.visited == ["http://example.test"]
        assert result == {"passed": 16, "total": 18}
    finally:
        loop.close()


def test_evaluate_preserves_falsy_values_through_the_json_roundtrip():
    # The whole reason for JSON.stringify: nodriver's bare-value return drops falsy 0/false
    # (``if remote_object.value:``). A JSON string "0"/"false" round-trips faithfully.
    loop = asyncio.new_event_loop()
    try:
        tab = FakeTab({_wrap_script("return 0"): "0", _wrap_script("return 1 === 2"): "false"})
        handle = NodriverHandle(tab, loop)

        assert handle.evaluate("return 0") == 0
        assert handle.evaluate("return 1 === 2") is False
    finally:
        loop.close()


def test_evaluate_returns_none_for_a_non_string_result():
    # JSON.stringify(undefined) is undefined (not a string) -> decode to None; detectors then
    # treat it as an unusable signal (they raise) rather than crash.
    loop = asyncio.new_event_loop()
    try:
        handle = NodriverHandle(FakeTab(), loop)  # unknown expr -> FakeTab returns None
        assert handle.evaluate("return whatever") is None
    finally:
        loop.close()


def test_quit_invokes_on_quit_callback():
    loop = asyncio.new_event_loop()
    calls = []
    handle = NodriverHandle(FakeTab(), loop, on_quit=lambda: calls.append("torn down"))

    handle.quit()
    loop.close()

    assert calls == ["torn down"]
