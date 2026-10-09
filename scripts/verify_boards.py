"""Check every proposed board against the live APIs.

Usage:
    python scripts/verify_boards.py              # all candidates (~20-40 minutes)
    python scripts/verify_boards.py --limit 10   # first 10 candidates, for testing

Input:
    companies/board_proposals.csv    from scripts/match_boards.py

Output:
    companies/verified_boards.csv    one row per candidate with status:
        verified      board found, inventory match or company name confirmed
        needs_review  slug guess with postings; confirm by hand
                      that it's the right company
        not_found     no proposed board has postings; goes to manual lookup
        error         a request failed; re-run later
"""

from __future__ import annotations

import argparse
import csv
import time
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

from hiring_pipeline.companies import Proposal
from hiring_pipeline.verification import check_board, make_session, verify_company

PROPOSALS = Path("companies/board_proposals.csv")
OUTPUT = Path("companies/verified_boards.csv")
SECONDS_BETWEEN_REQUESTS = 1.0
COLUMNS = [
    "company_name",
    "stratum",
    "status",
    "platform",
    "board_slug",
    "match_method",
    "open_postings",
    "board_company",
    "sample_titles",
    "checked_at",
]


def load_proposals() -> dict[tuple[str, str], list[Proposal]]:
    """Group proposals by (company, stratum), in attempt order."""
    grouped: dict[tuple[str, str], list[tuple[int, Proposal]]] = defaultdict(list)
    with PROPOSALS.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            proposal = Proposal(row["platform"], row["board_slug"], row["match_method"])
            grouped[(row["company_name"], row["stratum"])].append(
                (int(row["attempt"]), proposal)
            )
    return {key: [p for _, p in sorted(items)] for key, items in grouped.items()}


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--limit", type=int, help="only check the first N candidates")
    args = parser.parse_args()

    companies = list(load_proposals().items())[: args.limit]
    session = make_session()

    def polite_checker(platform: str, slug: str):
        time.sleep(SECONDS_BETWEEN_REQUESTS)
        return check_board(session, platform, slug)

    rows, counts = [], defaultdict(int)
    for i, ((name, stratum), proposals) in enumerate(companies, 1):
        result = verify_company(name, proposals, polite_checker)
        counts[result.status] += 1
        p, c = result.proposal, result.check
        print(f"[{i}/{len(companies)}] {name}: {result.status}")
        rows.append(
            {
                "company_name": name,
                "stratum": stratum,
                "status": result.status,
                "platform": p.platform if p else "",
                "board_slug": p.board_slug if p else "",
                "match_method": p.match_method if p else "",
                "open_postings": c.postings if c else "",
                "board_company": (c.board_company or "") if c else "",
                "sample_titles": " | ".join(c.sample_titles) if c else "",
                "checked_at": datetime.now(UTC).isoformat(timespec="seconds"),
            }
        )

    with OUTPUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nWrote {len(rows)} companies to {OUTPUT}")
    for status in ("verified", "needs_review", "not_found", "error"):
        print(f"  {status:<13} {counts[status]}")


if __name__ == "__main__":
    main()
