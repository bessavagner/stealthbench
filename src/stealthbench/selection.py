from __future__ import annotations

# Selection alias -> Config.label. Aliases are the short names an operator types;
# they map onto the (sometimes longer) canonical labels the runner records.
# Insertion order mirrors __main__'s configs list, so filtered output keeps that order.
CONFIG_NAMES: dict[str, str] = {
    "vanilla": "vanilla",
    "stealth": "selenium-stealth",
    "uc": "undetected-chromedriver",
    "camoufox": "camoufox",
    "nodriver": "nodriver",
}

# Detector selection names already match Detector.name exactly (all short).
DETECTOR_NAMES: tuple[str, ...] = ("tells", "botd", "sannysoft", "rebrowser", "creepjs")


def parse_selection(values, valid, kind):
    """Normalize repeated / comma-joined --config/--detector values to an ordered name list.

    ``values`` is argparse's ``append`` list (each item may itself be comma-joined), or
    None/empty when the operator selected nothing. Returns None for "no selection" (the
    caller keeps the full matrix), else a de-duplicated, first-seen-order list of names.
    Raises ValueError naming the unknown value(s) and the valid set on any bad name.
    """
    if not values:
        return None
    names = [n.strip() for v in values for n in v.split(",") if n.strip()]
    if not names:
        return None
    unknown = [n for n in names if n not in valid]
    if unknown:
        raise ValueError(
            f"unknown {kind}: {', '.join(unknown)}. "
            f"valid {kind}s: {', '.join(valid)}"
        )
    seen: dict[str, None] = {}
    for n in names:
        seen.setdefault(n, None)
    return list(seen)


def filter_configs(configs, names):
    """Subset of ``configs`` whose label matches the selected aliases.

    ``names is None`` -> the list is returned unchanged (identity), so a bare run is the
    same matrix as before. Canonical list order is preserved regardless of CLI flag order.
    """
    if names is None:
        return configs
    labels = {CONFIG_NAMES[n] for n in names}
    return [c for c in configs if c.label in labels]


def filter_detectors(detectors, names):
    """Subset of ``detectors`` whose name matches the selection; None -> identity."""
    if names is None:
        return detectors
    wanted = set(names)
    return [d for d in detectors if d.name in wanted]
