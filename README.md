# stealthbench

**A reproducible benchmark that puts _numbers_ on browser-automation stealth.**

![Python](https://img.shields.io/badge/python-3.12%2B-blue)
![Lint](https://img.shields.io/badge/lint-ruff-46a2f1)
![Tests](https://img.shields.io/badge/tests-14%20passing-brightgreen)
![Status](https://img.shields.io/badge/status-snapshot%2C%20not%20a%20guarantee-orange)

stealthbench scores stealth **configs** (how you set up an automated browser) against
open, self-hosted **detectors** (how a site decides you're a bot), and emits a
versioned results file plus a regenerable report. It measures *detectability* — it
never extracts anyone's data, and every detector runs on your own `localhost`.

The point is simple: instead of arguing about which automation setup is "stealthier,"
run all of them through the same detectors on the same machine and read the numbers.

## Latest snapshot

Chrome 149 · Linux · 3 trials · `results/20260706T155231.json`

| Config | Automation-tells passed | BotD verdict | CreepJS local lies |
|---|:---:|:---:|:---:|
| vanilla (stock Selenium) | 84% | caught (selenium) | 0 |
| selenium-stealth | 94% | caught (selenium) | 2 |
| undetected-chromedriver | 94% | **passed** | 0 |

![Automation-tells passed per config; bar colour = BotD verdict](results/pass-rate.png)

> **This is a snapshot, not a benchmark leaderboard.** These are the numbers from *one*
> environment on *one* day, run from a single IP. Detection evolves; a config that passes
> today can be caught next week. The value here is the **method and the reproducibility**,
> not the specific percentages — and every number above traces to a committed
> `results/*.json`.

## Scope & ethics

These techniques are for **legitimate automation and testing**: QA of your own web
apps, monitoring sites you operate, accessibility auditing, and research. To keep that
boundary concrete, stealthbench is built so it *can't* be pointed at someone else's
service as an attack tool:

- **Detectors are self-hosted on `localhost`** — nothing hammers a third party's
  anti-bot service, and the benchmark works fully offline.
- **Results are numbers only.** No IPs, no raw fingerprints, no page content is ever
  persisted. CreepJS contributes only its *local lie count* (its trust score needs
  CreepJS's own API, which a self-hosted copy can't reach).
- **It measures detectability; it never extracts data.** There is no crawler, no login,
  no target site in this codebase.

## How it works

A run is the cross-product **configs × detectors × trials**:

**Configs** (a stealth setup that builds a browser):

| Config | What it is |
|---|---|
| `vanilla` | Stock Selenium Chrome — the baseline. |
| `selenium-stealth` | Selenium + [`selenium-stealth`](https://pypi.org/project/selenium-stealth/) patches (webdriver flag, languages, vendor, WebGL, UA). |
| `undetected-chromedriver` | [`undetected-chromedriver`](https://pypi.org/project/undetected-chromedriver/), pinned to the installed Chrome major. |

**Detectors** (measure signals from a browser, return numbers):

| Detector | Signal |
|---|---|
| **tells panel** | A transparent panel of ~17 individual automation/fingerprint checks (`navigator.webdriver`, CDC props, WebGL hardware, plugin/mimetype counts, UA, permissions consistency, …). Reports `passed` / `total`. |
| **BotD** | [`@fingerprintjs/botd`](https://github.com/fingerprintjs/BotD) — returns whether it thinks you're a bot and, if so, which kind (`selenium`, `headless_chrome`, …). |
| **CreepJS** | A self-hosted copy of [CreepJS](https://github.com/abrahamjuliot/creepjs) — contributes its count of detected *lies* (fingerprint inconsistencies). |

The orchestrator runs each config through each detector for N trials, isolating errors
so one flaky detector or config can't abort the run, and folds everything into a typed,
versioned `BenchResult`. The report layer renders a markdown table + bar chart from that
result file.

## Architecture

The design rests on two `Protocol` seams that meet at a driver-agnostic `BrowserHandle`:

```
Config.build() ─┐                          ┌─ Detector.measure(handle)
                ├──▶  BrowserHandle  ◀──────┤
 (imports a       (goto / evaluate / quit)    (depends only on the
  driver SDK)                                   BrowserHandle Protocol)
                          │
                          ▼
        run_bench(configs, detectors, metadata) ──▶ BenchResult ──▶ report
             (pure, error-isolating)                 (versioned)     (table + chart)
```

- **Detectors are written against `BrowserHandle`, not a raw driver.** Adding a new
  browser stack (e.g. a Camoufox/Playwright arm) is a new `Config` + a new
  `BrowserHandle` implementation — **zero detector changes**.
- **Provider seam is enforced:** only `src/stealthbench/configs/` imports a driver SDK
  (`selenium` / `selenium-stealth` / `undetected-chromedriver`). Everything else —
  `core/`, `runner.py`, `report.py`, and every detector — depends only on the Protocols.
- **The pure core is unit-tested with fakes** (no browser required); the browser-touching
  configs and detectors are validated by the end-to-end run.

## Install

Requires **Python 3.12+**, [uv](https://docs.astral.sh/uv/), a real **Chrome/Chromium**,
and **Node.js** (to serve the BotD bundle).

```bash
git clone https://github.com/bessavagner/stealthbench.git
cd stealthbench
uv sync
```

## Run a benchmark

stealthbench talks to two local detector servers. Bring them up, then run the bench:

```bash
# 1. tells panel + BotD on :8901  (the BotD bundle is vendored via package-lock.json)
( cd src/stealthbench/detectors/assets && npm ci && python3 -m http.server 8901 ) &

# 2. CreepJS on :8902  (prebuilt bundle, no build step)
git clone --depth 1 https://github.com/abrahamjuliot/creepjs.git /tmp/creepjs
( cd /tmp/creepjs/docs && python3 -m http.server 8902 ) &

# 3. run the benchmark (headful; needs a display)
uv run python -m stealthbench --trials 3
```

This writes a fresh `results/<timestamp>.json`, a `results/summary.md` table, and a
`results/pass-rate.png` chart, and prints the summary. Options:

```
--trials N            number of trials (default 3)
--detector-host URL   tells + BotD host (default http://localhost:8901)
--creep-host  URL     CreepJS host        (default http://localhost:8902)
```

> Runs are **headful** by design (a headless browser is itself a strong tell). On a
> headless machine, run behind a virtual display such as `Xvfb`.

## Project layout

```
src/stealthbench/
├── core/            # BrowserHandle / Config / Detector Protocols + wait_until + BenchResult schema
├── configs/         # SeleniumHandle + vanilla / stealth / uc  (the ONLY driver-SDK importers)
├── detectors/       # tells / botd / creepjs  (+ self-hosted HTML assets)
├── runner.py        # run_bench: configs × detectors × trials, error-isolating
├── report.py        # summarize() + render_chart() from a results file
└── __main__.py      # CLI: python -m stealthbench
tests/               # pure-core unit tests (fakes; no browser) + detector contract tests
results/             # committed benchmark snapshots (json + summary.md + chart)
```

## Development

```bash
uv run pytest -q        # unit + detector-contract tests (no browser needed)
uv run ruff check .     # lint
```

The pure layers (core, runner, report, detector contracts) are test-driven and run
without a browser. Detectors **raise** on an invalid/failed signal so the runner records
an explicit error and the report shows `n/a` — a detector failure can never silently
masquerade as a stealth pass.

## Reproducibility

Every published figure is traceable: the CLI writes the raw `BenchResult` to
`results/<timestamp>.json`, and `summarize()` derives the table purely from it, so any
number can be recomputed from the committed data. Results are versioned
(`schema_version`) so older snapshots stay readable as the schema grows.

## Roadmap

A stealth-Firefox (Camoufox/Playwright) config arm, more detectors, CI, and packaging
are planned. The public backlog lands under `docs/plans/`.

## Acknowledgements

Built on the open detectors it measures against —
[BotD](https://github.com/fingerprintjs/BotD) by FingerprintJS and
[CreepJS](https://github.com/abrahamjuliot/creepjs) by Abraham Juliot — both self-hosted
here so nothing touches their live services.

## License

Licensing is still to be decided; until a `LICENSE` file is added, all rights are
reserved. If you'd like to use this, open an issue.
