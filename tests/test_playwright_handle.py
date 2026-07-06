from stealthbench.configs.playwright_handle import PlaywrightHandle, _wrap_script
from stealthbench.core.browser import BrowserHandle

# The proven translation (SBN-015 spike): wrap the detector's `return <expr>` as an
# arrow function AND bind `window` to the page's real window via Firefox's
# wrappedJSObject, so page-script expandos (__TELLS__/__BOTD__) resolve past the Xray.
_WRAPPED_TELLS = (
    "() => { return (function (window) { return window.__TELLS__ })"
    "(window.wrappedJSObject || window); }"
)
_WRAPPED_PROBE = (
    "() => { return (function (window) { return window.__BOTD__ !== undefined })"
    "(window.wrappedJSObject || window); }"
)


class FakePage:
    """Duck-typed Playwright page: records what it was asked, returns a canned value."""

    def __init__(self, value=None):
        self.value = value
        self.evaluated = None
        self.visited = None

    def goto(self, url):
        self.visited = url

    def evaluate(self, script):
        self.evaluated = script
        return self.value


def test_wrap_script_translates_return_convention():
    assert _wrap_script("return window.__TELLS__") == _WRAPPED_TELLS


def test_wrap_script_handles_the_wait_until_probe():
    assert _wrap_script("return window.__BOTD__ !== undefined") == _WRAPPED_PROBE


def test_wrap_script_reaches_page_window_past_firefox_xray():
    # The wrapper MUST route window access through wrappedJSObject; without it,
    # page-set globals read back undefined under Camoufox/Firefox (SBN-015 spike).
    assert "window.wrappedJSObject" in _wrap_script("return window.__TELLS__")


def test_evaluate_wraps_script_and_returns_page_value():
    page = FakePage(value={"passed": 15, "total": 17})
    handle = PlaywrightHandle(page)
    result = handle.evaluate("return window.__TELLS__")
    assert page.evaluated == _WRAPPED_TELLS
    assert result == {"passed": 15, "total": 17}


def test_goto_delegates_to_page():
    page = FakePage()
    PlaywrightHandle(page).goto("http://localhost:8901/tells.html")
    assert page.visited == "http://localhost:8901/tells.html"


def test_quit_invokes_on_quit_callback():
    calls = []
    PlaywrightHandle(FakePage(), on_quit=lambda: calls.append(True)).quit()
    assert calls == [True]


def test_quit_without_callback_is_a_noop():
    PlaywrightHandle(FakePage()).quit()  # must not raise


def test_handle_satisfies_browserhandle_protocol():
    assert isinstance(PlaywrightHandle(FakePage()), BrowserHandle)
