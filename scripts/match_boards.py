"""Propose job boards for every candidate company (no network calls).

Usage:
    python scripts/match_boards.py

Inputs:
    companies/candidates.csv
        from scripts/build_candidates.py
    data/ats_inventory/companies.csv
        board inventory published by ats-scrapers
        (https://storage.stapply.ai/jobhive/v1/companies.csv)

Output:
    companies/board_proposals.csv
    one row per proposed board, in order of preference;
    checked against the live APIs in the verification step
"""

from __future__ import annotations

import csv
from pathlib import Path

from hiring_pipeline.companies import load_inventory, propose_boards

CANDIDATES = Path("companies/candidates.csv")
INVENTORY = Path("data/ats_inventory/companies.csv")
OUTPUT = Path("companies/board_proposals.csv")
COLUMNS = [
    "company_name",
    "stratum",
    "attempt",
    "platform",
    "board_slug",
    "match_method",
]


def main() -> None:
    inventory = load_inventory(INVENTORY)
    print(f"Inventory: {len(inventory):,} company names on supported platforms")

    with CANDIDATES.open(newline="", encoding="utf-8") as f:
        candidates = list(csv.DictReader(f))

    rows, inventory_hits = [], 0
    for candidate in candidates:
        proposals = propose_boards(candidate["company_name"], inventory)
        inventory_hits += proposals[0].match_method == "inventory"
        for attempt, p in enumerate(proposals, 1):
            rows.append(
                {
                    "company_name": candidate["company_name"],
                    "stratum": candidate["stratum"],
                    "attempt": attempt,
                    "platform": p.platform,
                    "board_slug": p.board_slug,
                    "match_method": p.match_method,
                }
            )

    with OUTPUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Candidates: {len(candidates)}")
    print(f"  found in inventory: {inventory_hits}")
    print(f"  slug guesses only:  {len(candidates) - inventory_hits}")
    print(f"Wrote {len(rows)} proposals to {OUTPUT}")


if __name__ == "__main__":
    main()
