"""
Does playing at a faster pace actually make an NBA team better (higher offensive
rating, more wins) - or is pace irrelevant once you account for efficiency?

Reads data/nba_advanced_team_stats.csv (one row per team-season, produced by
scrape_nba_advanced_stats.py) and computes, per season:
  - league-average Pace (to show the historical pace trend / eras)
  - Pearson r: Pace vs WinPct
  - Pearson r: Pace vs ORtg (offensive rating)
  - Pearson r: NRtg vs WinPct (net rating - the "true" quality metric, for contrast)

Saves data/pace_efficiency_summary.csv and prints the headline numbers.
"""

import os

import numpy as np
import pandas as pd
from scipy import stats

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "..", "data")
IN_PATH = os.path.join(DATA_DIR, "nba_advanced_team_stats.csv")
OUT_PATH = os.path.join(DATA_DIR, "pace_efficiency_summary.csv")


def season_correlations(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for season, g in df.groupby("Season"):
        g = g.dropna(subset=["Pace", "WinPct", "ORtg", "NRtg"])
        if len(g) < 5:
            continue
        r_pace_win, _ = stats.pearsonr(g["Pace"], g["WinPct"])
        r_pace_ortg, _ = stats.pearsonr(g["Pace"], g["ORtg"])
        r_nrtg_win, _ = stats.pearsonr(g["NRtg"], g["WinPct"])
        rows.append(
            {
                "Season": season,
                "AvgPace": g["Pace"].mean(),
                "PaceStd": g["Pace"].std(),
                "r_pace_winpct": r_pace_win,
                "r_pace_ortg": r_pace_ortg,
                "r_nrtg_winpct": r_nrtg_win,
                "n_teams": len(g),
            }
        )
    return pd.DataFrame(rows).sort_values("Season")


def main():
    df = pd.read_csv(IN_PATH)
    summary = season_correlations(df)
    os.makedirs(DATA_DIR, exist_ok=True)
    summary.to_csv(OUT_PATH, index=False)

    print(f"Seasons analyzed: {summary['Season'].min()}-{summary['Season'].max()} "
          f"({len(summary)} seasons, {int(summary['n_teams'].sum())} team-seasons)")
    print()
    print("--- League pace trend ---")
    print(f"Avg pace {summary['Season'].min()}: {summary.iloc[0]['AvgPace']:.1f}")
    print(f"Lowest avg pace season: {summary.loc[summary['AvgPace'].idxmin(), 'Season']} "
          f"({summary['AvgPace'].min():.1f})")
    print(f"Avg pace {summary['Season'].max()}: {summary.iloc[-1]['AvgPace']:.1f}")
    print()
    print("--- Does pace predict winning? (within-season correlation, then averaged) ---")
    print(f"Mean r(Pace, WinPct) across seasons: {summary['r_pace_winpct'].mean():.3f} "
          f"(std {summary['r_pace_winpct'].std():.3f})")
    print(f"Mean r(Pace, ORtg) across seasons:   {summary['r_pace_ortg'].mean():.3f} "
          f"(std {summary['r_pace_ortg'].std():.3f})")
    print(f"Mean r(NRtg, WinPct) across seasons: {summary['r_nrtg_winpct'].mean():.3f} "
          f"(std {summary['r_nrtg_winpct'].std():.3f})  <- for contrast")
    print()

    # pooled, era-adjusted view: de-mean Pace and WinPct within season so a
    # "fast 80s vs slow 90s" league shift doesn't masquerade as a within-season effect
    df2 = df.dropna(subset=["Pace", "WinPct"]).copy()
    df2["Pace_dm"] = df2["Pace"] - df2.groupby("Season")["Pace"].transform("mean")
    df2["WinPct_dm"] = df2["WinPct"] - df2.groupby("Season")["WinPct"].transform("mean")
    r_pooled, p_pooled = stats.pearsonr(df2["Pace_dm"], df2["WinPct_dm"])
    print(f"Pooled era-adjusted r(Pace, WinPct) across all {len(df2)} team-seasons: "
          f"{r_pooled:.3f} (p={p_pooled:.3g})")


if __name__ == "__main__":
    main()
