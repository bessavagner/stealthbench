import matplotlib

matplotlib.use("Agg")  # headless-safe backend for CI

PALETTE = {"passed": "#2e7d32", "caught": "#c62828"}

# Trend chart: neutral per-config series identity (NOT pass/caught semantics).
# tab10-derived, colorblind-friendly, no green/red so it can't be misread as a verdict.
TREND_PALETTE = ["#1f77b4", "#ff7f0e", "#9467bd", "#8c564b"]  # blue, orange, purple, brown
TREND_LINESTYLES = ["-", "--", "-.", ":"]
TREND_MARKERS = ["o", "s", "^", "D"]


def apply() -> None:
    import matplotlib.pyplot as plt

    plt.rcParams.update({"figure.dpi": 120, "font.size": 11, "axes.spines.top": False,
                         "axes.spines.right": False})
