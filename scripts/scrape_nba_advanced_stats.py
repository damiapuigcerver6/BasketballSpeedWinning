"""
Scrapes the "Advanced Stats" team table (Pace, ORtg, DRtg, SRS, W/L, ...)
for every NBA season in a given range from Basketball-Reference.

Usage:
    python scrape_nba_advanced_stats.py --start 1980 --end 2025

Saves:
    data/raw/NBA_<year>.html   (cached raw page, so re-runs don't re-hit the site)
    data/nba_advanced_team_stats.csv  (combined, cleaned dataset)
"""

import argparse
import os
import time

import pandas as pd
import requests

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
BASE_URL = "https://www.basketball-reference.com/leagues/NBA_{year}.html"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "..", "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")


def fetch_season_html(year: int) -> str:
    os.makedirs(RAW_DIR, exist_ok=True)
    cache_path = os.path.join(RAW_DIR, f"NBA_{year}.html")
    if os.path.exists(cache_path):
        with open(cache_path, encoding="utf-8") as f:
            return f.read()

    url = BASE_URL.format(year=year)
    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    with open(cache_path, "w", encoding="utf-8") as f:
        f.write(resp.text)
    time.sleep(3.5)  # be polite to basketball-reference's rate limits
    return resp.text


def parse_advanced_table(html: str, year: int) -> pd.DataFrame:
    tables = pd.read_html(html, attrs={"id": "advanced-team"})
    df = tables[0]
    # flatten the MultiIndex columns (Basketball-Reference groups Four Factors
    # under extra header rows) down to their leaf labels
    df.columns = [c[-1] if isinstance(c, tuple) else c for c in df.columns]
    df = df.loc[:, ~df.columns.str.startswith("Unnamed")]
    # drop the mid-table repeated header row ("League Average" separator etc.)
    df = df[df["Team"].notna() & (df["Team"] != "Team")]
    df["Team"] = df["Team"].str.replace("*", "", regex=False).str.strip()
    df["Season"] = year
    for col in ["W", "L", "MOV", "SRS", "ORtg", "DRtg", "NRtg", "Pace"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["WinPct"] = df["W"] / (df["W"] + df["L"])
    return df[["Season", "Team", "W", "L", "WinPct", "MOV", "SRS", "ORtg", "DRtg", "NRtg", "Pace"]]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=1980)
    parser.add_argument("--end", type=int, default=2025)
    args = parser.parse_args()

    frames = []
    for year in range(args.start, args.end + 1):
        print(f"Fetching {year}...")
        try:
            html = fetch_season_html(year)
            frames.append(parse_advanced_table(html, year))
        except Exception as e:
            print(f"  skipped {year}: {e}")

    combined = pd.concat(frames, ignore_index=True)
    os.makedirs(DATA_DIR, exist_ok=True)
    out_path = os.path.join(DATA_DIR, "nba_advanced_team_stats.csv")
    combined.to_csv(out_path, index=False)
    print(f"Saved {len(combined)} rows to {out_path}")


if __name__ == "__main__":
    main()
