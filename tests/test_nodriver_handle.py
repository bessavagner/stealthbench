import asyncio

from stealthbench.configs.nodriver_handle import NodriverHandle, _wrap_script


class FakeTab:
    """Duck-typed nodriver tab: async get/evaluate, canned returns by expression."""

    def __init__(self, returns=None):
        self.returns = returns or {}
        self.visited = []

    async def get(self, url):
        self.visited.append(url)

    async def evaluate(self, expr, await_promise=False, return_by_value=True):
        return self.returns.get(expr)


def test_wrap_script_wraps_return_body_as_an_iife_expression():
    assert _wrap_script("return window.__BOTD__") == "(() => { return window.__BOTD__ })()"


def test_goto_and_evaluate_drive_the_async_tab_on_the_loop():
    loop = asyncio.new_event_loop()
    try:
        expr = _wrap_script("return 1 + 1")
        tab = FakeTab({expr: 2})
        handle = NodriverHandle(tab, loop)

        handle.goto("http://example.test")
        result = handle.evaluate("return 1 + 1")

        assert tab.visited == ["http://example.test"]
        assert result == 2
    finally:
        loop.close()


def test_quit_invokes_on_quit_callback():
    loop = asyncio.new_event_loop()
    calls = []
    handle = NodriverHandle(FakeTab(), loop, on_quit=lambda: calls.append("torn down"))

    handle.quit()
    loop.close()

    assert calls == ["torn down"]
