# stealthbench

A reproducible benchmark that puts **numbers** on browser-automation stealth.
It scores stealth *configs* against open, self-hosted *detectors* (a transparent
automation-tells panel, BotD, CreepJS) and emits versioned results plus a
regenerable report. It measures detectability; it does not extract anyone's data.

## Scope & ethics

These techniques are for **legitimate automation and testing** — QA of your own
apps, monitoring sites you operate, accessibility, and research. Detectors are
**self-hosted on localhost**, so nothing hammers third-party anti-bot services.
Every published number is a snapshot of one environment on one day, not a
guarantee — detection evolves.

## Run

See `docs/.ai/plans/` for the build plan. Quickstart lands in Task 7.
