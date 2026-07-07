from __future__ import annotations

import argparse
import subprocess
import threading
import time
import urllib.error
import urllib.request
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ASSETS_DIR = Path(__file__).resolve().parent / "detectors" / "assets"
CREEPJS_REPO = "https://github.com/abrahamjuliot/creepjs.git"


def ensure_npm(assets_dir=ASSETS_DIR, run=subprocess.run):
    """Run ``npm ci`` in the vendored-assets dir once, only if node_modules is absent.

    Mirrors the README bring-up step. Returns True if it ran, False if already present.
    """
    if (Path(assets_dir) / "node_modules").exists():
        return False
    run(["npm", "ci"], cwd=str(assets_dir), check=True)
    return True


def ensure_creepjs(creep_dir, run=subprocess.run):
    """Fetch CreepJS once into ``creep_dir`` (skip if present); return its ``docs/`` dir.

    A one-time SETUP fetch of an open MIT bundle (the same clone the README documents).
    The bench never contacts CreepJS's origin at run time — only the localhost copy this
    serves. Fetching once, not per bench run, keeps the self-host-only invariant intact.
    """
    creep_dir = Path(creep_dir)
    if not creep_dir.exists():
        run(
            ["git", "clone", "--depth", "1", CREEPJS_REPO, str(creep_dir)],
            check=True,
        )
    return creep_dir / "docs"


def serve_dir(directory, port):
    """Start a threaded static file server for ``directory`` on ``port``; return the server."""
    handler = partial(SimpleHTTPRequestHandler, directory=str(directory))
    httpd = ThreadingHTTPServer(("", port), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def healthcheck(url, attempts=20, delay=0.25):
    """GET ``url`` until it returns 200; raise RuntimeError once attempts are exhausted."""
    last = None
    for _ in range(attempts):
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if resp.status == 200:
                    return True
        except (urllib.error.URLError, OSError) as exc:  # server not up yet
            last = exc
        time.sleep(delay)
    raise RuntimeError(f"health check failed for {url}: {last}")


def urls(detector_port, creep_port):
    """The two localhost URLs the bench defaults to."""
    return f"http://localhost:{detector_port}", f"http://localhost:{creep_port}"


def main():
    p = argparse.ArgumentParser(
        prog="stealthbench.serve",
        description="Start both local detector servers and serve CreepJS "
        "(fetched once), then health-check both.",
    )
    p.add_argument("--detector-port", type=int, default=8901)
    p.add_argument("--creep-port", type=int, default=8902)
    p.add_argument(
        "--creep-dir",
        default="/tmp/creepjs",
        help="local dir to fetch/keep the CreepJS bundle (fetched once, then reused)",
    )
    args = p.parse_args()

    ensure_npm()
    creep_docs = ensure_creepjs(Path(args.creep_dir))

    serve_dir(ASSETS_DIR, args.detector_port)
    serve_dir(creep_docs, args.creep_port)

    det_url, creep_url = urls(args.detector_port, args.creep_port)
    healthcheck(det_url + "/")  # dir listing (assets/ has no index) returns 200
    healthcheck(creep_url + "/")  # CreepJS docs/index.html returns 200

    print(f"detectors ready:  {det_url}   (tells / botd / sannysoft / rebrowser)")
    print(f"creepjs ready:    {creep_url}")
    print(f"run the bench:    python -m stealthbench "
          f"--detector-host {det_url} --creep-host {creep_url}")
    print("serving… Ctrl-C to stop.")
    try:
        threading.Event().wait()  # block until interrupted; servers run in daemon threads
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
