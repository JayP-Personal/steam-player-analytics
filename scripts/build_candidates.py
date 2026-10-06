"""Build the candidates file from the three source lists in ADR 0003.

Sources:
  early   Y Combinator companies, via the community-maintained yc-oss API
          (https://github.com/yc-oss/api): active, hiring, recent batches,
          randomly sampled with a fixed seed so the sample is reproducible.
  growth  Forbes Cloud 100: copied by hand from forbes.com/lists/cloud100 into
          companies/sources/forbes_cloud100.csv (columns: rank, company_name).
  public  S&P 500 constituents from Wikipedia, filtered by GICS sector.

Usage:
    python scripts/build_candidates.py
    python scripts/build_candidates.py --yc-min-year 2024 --yc-sample 150 --seed 42

Output:
    companies/candidates.csv
"""

from __future__ import annotations

import argparse
import re
from datetime import UTC, datetime
from io import StringIO
from pathlib import Path

import pandas as pd
import requests

YC_HIRING_URL = "https://yc-oss.github.io/api/companies/hiring.json"
SP500_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
FORBES_FILE = Path("companies/sources/forbes_cloud100.csv")
OUT_FILE = Path("companies/candidates.csv")
HEADERS = {"User-Agent": "tech-hiring-signals (portfolio research project)"}

# Big tech names like Alphabet and Meta are classified outside the IT sector,
# so the public stratum also includes these sub-industries.
SP500_SECTORS = {"Information Technology"}
SP500_SUB_INDUSTRIES = {"Interactive Media & Services", "Broadline Retail"}

COLUMNS = [
    "company_name",
    "website",
    "stratum",
    "source_list",
    "source_detail",
    "retrieved_on",
]


def batch_year(batch: str | None) -> int | None:
    match = re.search(r"(19|20)\d{2}", batch or "")
    return int(match.group()) if match else None


def yc_candidates(min_year: int, top: int) -> pd.DataFrame:
    companies = requests.get(YC_HIRING_URL, headers=HEADERS, timeout=60).json()
    eligible = [
        c
        for c in companies
        if c.get("status") == "Active"
        and c.get("isHiring")
        and (batch_year(c.get("batch")) or 0) >= min_year
        and c.get("team_size")  # drop companies with no team size
    ]
    # Largest first; ties broken alphabetically so the selection is deterministic
    eligible.sort(key=lambda c: (-c["team_size"], c["name"].lower()))
    chosen = eligible[:top]
    print(
        f"YC: {len(eligible)} eligible with a team size, kept the largest {len(chosen)}"
    )
    print(
        f"Smallest team kept: {chosen[-1]['team_size']} people"
        if chosen
        else "No companies kept"
    )
    return pd.DataFrame(
        {
            "company_name": [c["name"] for c in chosen],
            "website": [c.get("website", "") for c in chosen],
            "stratum": "early",
            "source_list": "YC hiring (yc-oss API)",
            "source_detail": [
                f"{c.get('batch', '')}, team size {c['team_size']}" for c in chosen
            ],
        }
    )


def forbes_candidates() -> pd.DataFrame:
    df = pd.read_csv(FORBES_FILE)
    print(f"Forbes Cloud 100: {len(df)} companies from {FORBES_FILE}")
    return pd.DataFrame(
        {
            "company_name": df["company_name"],
            "website": "",
            "stratum": "growth",
            "source_list": "Forbes Cloud 100 2025",
            "source_detail": "rank " + df["rank"].astype(str),
        }
    )


def sp500_candidates() -> pd.DataFrame:
    html = requests.get(SP500_URL, headers=HEADERS, timeout=60).text
    table = pd.read_html(StringIO(html))[0]
    keep = table["GICS Sector"].isin(SP500_SECTORS) | table["GICS Sub-Industry"].isin(
        SP500_SUB_INDUSTRIES
    )
    df = table[keep]
    print(f"S&P 500: {len(df)} companies in selected sectors")
    return pd.DataFrame(
        {
            "company_name": df["Security"],
            "website": "",
            "stratum": "public",
            "source_list": "S&P 500 (Wikipedia)",
            "source_detail": df["GICS Sub-Industry"],
        }
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--yc-min-year", type=int, default=2024)
    parser.add_argument("--yc-top", type=int, default=150)
    args = parser.parse_args()

    candidates = pd.concat(
        [
            yc_candidates(args.yc_min_year, args.yc_top),
            forbes_candidates(),
            sp500_candidates(),
        ],
        ignore_index=True,
    )
    candidates["retrieved_on"] = datetime.now(UTC).date().isoformat()
    candidates = candidates.drop_duplicates(subset="company_name", keep="first")[
        COLUMNS
    ]

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    candidates.to_csv(OUT_FILE, index=False)
    print(f"\nWrote {len(candidates)} candidates to {OUT_FILE}")
    print(candidates["stratum"].value_counts().to_string())


if __name__ == "__main__":
    main()
