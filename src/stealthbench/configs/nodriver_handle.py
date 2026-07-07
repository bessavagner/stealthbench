from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any


def _wrap_script(script: str) -> str:
    """Translate a Selenium-style ``return <expr>`` script into a JSON-returning JS expression.

    nodriver's ``tab.evaluate`` runs a JS *expression* (Runtime.evaluate), not a statement body
    that may ``return`` (as Selenium's ``execute_script`` does), so the detector's ``return …``
    body is wrapped in a zero-arg arrow IIFE. It is further wrapped in ``JSON.stringify`` to
    sidestep two nodriver quirks that otherwise corrupt the result: nodriver's ``return_by_value``
    unwrap tests ``if remote_object.value:`` — dropping *falsy* values (``0`` / ``false`` / ``""``)
    — and its default deep-serialization leaves plain objects wrapped in a ``RemoteObject``. By
    returning a primitive JSON *string* (which nodriver relays faithfully), the handle can
    ``json.loads`` it back to the exact Python value. Detectors keep their ``"return …"``
    convention unchanged.
    """
    return f"JSON.stringify((() => {{ {script} }})())"


class NodriverHandle:
    """BrowserHandle over a nodriver async tab. Lives under ``configs/`` — the only place a
    browser SDK is used. It never imports nodriver; it duck-types on the tab and drives each
    async call to completion on a private event loop, so the sync ``BrowserHandle`` contract
    holds and the translation logic is unit-testable with a fake tab.

    ``on_quit`` tears down whatever built the tab (the browser + the loop); the runner calls
    ``quit()`` in a ``finally``.
    """

    def __init__(self, tab: Any, loop: Any, on_quit: Callable[[], None] | None = None):
        self._tab = tab
        self._loop = loop
        self._on_quit = on_quit

    def _run(self, coro: Any) -> Any:
        return self._loop.run_until_complete(coro)

    def goto(self, url: str) -> None:
        self._run(self._tab.get(url))

    def evaluate(self, script: str) -> Any:
        raw = self._run(
            self._tab.evaluate(_wrap_script(script), await_promise=True, return_by_value=True)
        )
        # A well-formed script returns a JSON string (see _wrap_script). Anything else — e.g. a
        # JS ``undefined`` result, which ``JSON.stringify`` renders as ``undefined`` (not a
        # string) — decodes to ``None``; detectors already treat a non-dict signal as unusable.
        if not isinstance(raw, str):
            return None
        return json.loads(raw)

    def quit(self) -> None:
        if self._on_quit is not None:
            self._on_quit()
