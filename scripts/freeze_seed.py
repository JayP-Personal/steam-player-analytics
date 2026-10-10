"""Freeze verified job boards into the
    dbt seed the collection pipeline reads.

Usage:
    python scripts/freeze_seed.py
        # refuses to overwrite an existing seed
    python scripts/freeze_seed.py --force
        # rebuild deliberately

Inputs:
    companies/verified_boards.csv
        from scripts/verify_boards.py (after manual review)
    companies/candidates.csv
        for each company's source list

Output:
    dbt/seeds/companies.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
from datetime import UTC, datetime
from pathlib import Path

VERIFIED = Path("companies/verified_boards.csv")
CANDIDATES = Path("companies/candidates.csv")
SEED = Path("dbt/seeds/companies.csv")
COLUMNS = [
    "board_id",
    "company_name",
    "platform",
    "board_slug",
    "stratum",
    "source_list",
    "added_on",
    "status",
]


def read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--force", action="store_true", help="overwrite an existing seed"
    )
    args = parser.parse_args()

    if SEED.exists() and not args.force:
        sys.exit(
            f"{SEED} already exists. The seed is frozen; use --force to rebuild it."
        )

    source_lists = {
        row["company_name"]: row["source_list"] for row in read_csv(CANDIDATES)
    }
    added_on = datetime.now(UTC).date().isoformat()

    rows, seen = [], set()
    for row in read_csv(VERIFIED):
        if row["status"] != "verified":
            continue
        board_id = f"{row['platform']}:{row['board_slug']}"
        if board_id in seen:  # two candidates resolved to the same board
            print(f"Skipping duplicate board {board_id} ({row['company_name']})")
            continue
        seen.add(board_id)
        rows.append(
            {
                "board_id": board_id,
                "company_name": row["company_name"],
                "platform": row["platform"],
                "board_slug": row["board_slug"],
                "stratum": row["stratum"],
                "source_list": source_lists.get(row["company_name"], ""),
                "added_on": added_on,
                "status": "active",
            }
        )

    rows.sort(key=lambda r: (r["stratum"], r["company_name"].lower()))
    SEED.parent.mkdir(parents=True, exist_ok=True)
    with SEED.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} boards to {SEED}")


if __name__ == "__main__":
    main()
