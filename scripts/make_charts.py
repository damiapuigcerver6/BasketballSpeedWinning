"""
Generates the three charts for the "does pace win games?" LinkedIn post,
styled with the validated dataviz palette (see dataviz skill / palette.md).

Reads data/nba_advanced_team_stats.csv and data/pace_efficiency_summary.csv
(both produced by the scrape/analyze scripts) and writes PNGs to figures/.
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "..", "data")
FIG_DIR = os.path.join(SCRIPT_DIR, "..", "figures")
os.makedirs(FIG_DIR, exist_ok=True)

# --- palette (light mode, from the dataviz skill's validated default) ---
SURFACE = "#fcfcfb"
INK_PRIMARY = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GRID = "#e1e0d9"
BASELINE = "#c3c2b7"
BLUE = "#2a78d6"      # slot 1 - categorical
ORANGE = "#eb6834"    # slot 2 - categorical
AQUA = "#1baf7a"       # slot 3 - categorical

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Segoe UI", "Arial", "sans-serif"],
    "axes.edgecolor": BASELINE,
    "axes.labelcolor": INK_SECONDARY,
    "text.color": INK_PRIMARY,
    "xtick.color": INK_MUTED,
    "ytick.color": INK_MUTED,
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE,
})


def add_header(fig, title: str, subtitle: str):
    """Two-line header (bold title + muted subtitle) reserved above the axes,
    so it never collides with the plot area regardless of figure size."""
    fig.suptitle(title, x=0.02, y=0.99, ha="left", va="top",
                 fontsize=15, color=INK_PRIMARY, fontweight="bold")
    fig.text(0.02, 0.905, subtitle, ha="left", va="top",
              fontsize=10.5, color=INK_SECONDARY)


def chart_pace_trend(summary: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(9, 5.5), dpi=200)
    ax.plot(summary["Season"], summary["AvgPace"], color=BLUE, linewidth=2.5, solid_capstyle="round")
    ax.grid(axis="y", color=GRID, linewidth=1, zorder=0)
    ax.set_axisbelow(True)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color(BASELINE)
    ax.spines["bottom"].set_color(BASELINE)

    # annotate key eras
    low_idx = summary["AvgPace"].idxmin()
    low_season = summary.loc[low_idx, "Season"]
    low_pace = summary.loc[low_idx, "AvgPace"]
    ax.annotate(
        f"Dead-ball era low:\n{low_season} ({low_pace:.1f} poss/48min)",
        xy=(low_season, low_pace), xytext=(low_season - 6, low_pace - 6),
        fontsize=9.5, color=INK_SECONDARY,
        arrowprops=dict(arrowstyle="-", color=INK_MUTED, lw=1),
    )
    last = summary.iloc[-1]
    ax.annotate(
        f"{int(last['Season'])}: {last['AvgPace']:.1f}",
        xy=(last["Season"], last["AvgPace"]), xytext=(-55, 10), textcoords="offset points",
        fontsize=9.5, color=INK_SECONDARY,
    )

    add_header(fig, "The NBA got slow, then fast again",
               "League-average possessions per 48 minutes, by season")
    ax.set_ylabel("Pace (possessions / 48 min)")
    fig.tight_layout(rect=[0, 0, 1, 0.87])
    fig.savefig(os.path.join(FIG_DIR, "01_pace_trend.png"))
    plt.close(fig)


def chart_correlation_over_time(summary: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(9, 5.5), dpi=200)
    ax.axhline(0, color=BASELINE, linewidth=1)
    ax.plot(summary["Season"], summary["r_nrtg_winpct"], color=AQUA, linewidth=2.5,
            solid_capstyle="round", label="Net rating -> Win%")
    ax.plot(summary["Season"], summary["r_pace_winpct"], color=ORANGE, linewidth=2.5,
            solid_capstyle="round", label="Pace -> Win%")
    ax.grid(axis="y", color=GRID, linewidth=1, zorder=0)
    ax.set_axisbelow(True)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color(BASELINE)
    ax.spines["bottom"].set_color(BASELINE)
    ax.set_ylim(-1, 1)
    ax.set_xlim(summary["Season"].min() - 1, summary["Season"].max() + 3.5)

    # direct labels instead of a boxed legend
    ax.text(summary["Season"].iloc[-1] + 0.6, summary["r_nrtg_winpct"].iloc[-1], "Net rating\n→ Win%",
            color=AQUA, fontsize=10, va="center", fontweight="bold")
    ax.text(summary["Season"].iloc[-1] + 0.6, summary["r_pace_winpct"].iloc[-1], "Pace\n→ Win%",
            color=ORANGE, fontsize=10, va="center", fontweight="bold")

    add_header(fig, "Efficiency wins games. Pace doesn't.",
               "Correlation with regular-season win%, computed within each season")
    ax.set_ylabel("Pearson r")
    fig.tight_layout(rect=[0, 0, 1, 0.87])
    fig.savefig(os.path.join(FIG_DIR, "02_correlation_over_time.png"))
    plt.close(fig)


def chart_scatter_latest(df: pd.DataFrame, season: int):
    g = df[df["Season"] == season].dropna(subset=["Pace", "WinPct"])
    fig, ax = plt.subplots(figsize=(7, 6.5), dpi=200)
    ax.scatter(g["Pace"], g["WinPct"], s=70, color=BLUE, alpha=0.85, edgecolor=SURFACE, linewidth=1.2, zorder=3)

    # trend line
    coeffs = np.polyfit(g["Pace"], g["WinPct"], 1)
    xs = np.linspace(g["Pace"].min(), g["Pace"].max(), 50)
    ax.plot(xs, np.polyval(coeffs, xs), color=INK_MUTED, linewidth=1.5, linestyle=(0, (4, 3)), zorder=2)

    r = np.corrcoef(g["Pace"], g["WinPct"])[0, 1]
    ax.text(0.03, 0.05, f"r = {r:.2f}", transform=ax.transAxes, fontsize=12, color=INK_SECONDARY, fontweight="bold")

    ax.grid(color=GRID, linewidth=1, zorder=0)
    ax.set_axisbelow(True)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color(BASELINE)
    ax.spines["bottom"].set_color(BASELINE)

    add_header(fig, f"{season}: fast teams don't win more",
               "Every NBA team, one season — pace vs. win percentage")
    ax.set_xlabel("Pace (possessions / 48 min)")
    ax.set_ylabel("Win %")
    fig.tight_layout(rect=[0, 0, 1, 0.87])
    fig.savefig(os.path.join(FIG_DIR, "03_scatter_latest_season.png"))
    plt.close(fig)


def main():
    summary = pd.read_csv(os.path.join(DATA_DIR, "pace_efficiency_summary.csv"))
    df = pd.read_csv(os.path.join(DATA_DIR, "nba_advanced_team_stats.csv"))

    chart_pace_trend(summary)
    chart_correlation_over_time(summary)
    chart_scatter_latest(df, season=int(summary["Season"].max()))
    print(f"Charts written to {FIG_DIR}")


if __name__ == "__main__":
    main()
