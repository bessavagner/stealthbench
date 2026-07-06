import matplotlib

matplotlib.use("Agg")  # headless-safe backend for CI

PALETTE = {"passed": "#2e7d32", "caught": "#c62828", "bar": "#37474f"}


def apply() -> None:
    import matplotlib.pyplot as plt

    plt.rcParams.update({"figure.dpi": 120, "font.size": 11, "axes.spines.top": False,
                         "axes.spines.right": False})
