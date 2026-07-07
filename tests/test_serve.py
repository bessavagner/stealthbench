from stealthbench import serve


class _RecRun:
    """Records subprocess-style calls without executing anything."""

    def __init__(self):
        self.calls = []

    def __call__(self, cmd, **kwargs):
        self.calls.append((cmd, kwargs))
        return 0


def test_ensure_creepjs_skips_clone_when_present(tmp_path):
    creep = tmp_path / "creepjs"
    (creep / "docs").mkdir(parents=True)  # already fetched
    rec = _RecRun()
    docs = serve.ensure_creepjs(creep, run=rec)
    assert rec.calls == []  # no network fetch on a second bring-up
    assert docs == creep / "docs"


def test_ensure_creepjs_clones_once_when_absent(tmp_path):
    creep = tmp_path / "creepjs"  # missing
    rec = _RecRun()
    docs = serve.ensure_creepjs(creep, run=rec)
    assert len(rec.calls) == 1
    cmd, _ = rec.calls[0]
    assert cmd[:4] == ["git", "clone", "--depth", "1"]
    assert cmd[-1] == str(creep)
    assert docs == creep / "docs"


def test_ensure_npm_skips_when_node_modules_present(tmp_path):
    (tmp_path / "node_modules").mkdir()
    rec = _RecRun()
    assert serve.ensure_npm(tmp_path, run=rec) is False
    assert rec.calls == []


def test_ensure_npm_runs_when_absent(tmp_path):
    rec = _RecRun()
    assert serve.ensure_npm(tmp_path, run=rec) is True
    cmd, kwargs = rec.calls[0]
    assert cmd == ["npm", "ci"]
    assert kwargs.get("cwd") == str(tmp_path)


def test_urls_match_the_bench_defaults():
    det, creep = serve.urls(8901, 8902)
    assert det == "http://localhost:8901"
    assert creep == "http://localhost:8902"


def test_assets_dir_points_at_vendored_bundle():
    assert serve.ASSETS_DIR.name == "assets"
    assert serve.ASSETS_DIR.parent.name == "detectors"
