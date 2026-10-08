"""Match candidate companies to job board slugs.

Pure logic, no network calls. Every proposal produced here is checked
against the live board API in a separate verification step.
"""

from __future__ import annotations

import csv
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

PLATFORMS = ("greenhouse", "lever", "ashby")

_PARENTHESES = re.compile(r"\([^)]*\)")
_NON_ALNUM = re.compile(r"[^a-z0-9]+")
_SUFFIXES = re.compile(
    r"\b(inc|incorporated|corp|corporation|co|company|llc|ltd|limited|plc"
    r"|holdings|group|technologies|technology|labs|hq)\b"
)


@dataclass(frozen=True)
class Proposal:
    """A possible job board for a candidate, to be verified later."""

    platform: str
    board_slug: str
    match_method: str  # "inventory" or "slug_guess"


def normalize_name(name: str) -> str:
    """Reduce a company name to a comparable form.

    "Airbnb, Inc." -> "airbnb"; "Alphabet Inc. (Class A)" -> "alphabet".
    """
    text = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    text = text.lower().replace("&", " and ").replace("'", "")
    text = _PARENTHESES.sub(" ", text)
    text = _NON_ALNUM.sub(" ", text)
    text = _SUFFIXES.sub(" ", text)
    return " ".join(text.split())


def slug_guesses(name: str) -> list[str]:
    """Likely board slugs for a company name, most likely first."""
    words = normalize_name(name).split()
    if not words:
        return []
    guesses = ["".join(words), "-".join(words), words[0], "".join(words) + "hq"]
    return list(dict.fromkeys(guesses))  # drop duplicates, keep order


def load_inventory(path: Path) -> dict[str, list[Proposal]]:
    """Index the board inventory by normalized company name.

    Expects a CSV with columns ats, name, slug. Rows for platforms outside
    PLATFORMS are skipped.
    """
    index: dict[str, list[Proposal]] = {}
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            platform = row["ats"].strip().lower()
            slug = row["slug"].strip()
            key = normalize_name(row["name"])
            if platform in PLATFORMS and slug and key:
                proposal = Proposal(platform, slug, "inventory")
                index.setdefault(key, []).append(proposal)
    return index


def propose_boards(name: str, inventory: dict[str, list[Proposal]]) -> list[Proposal]:
    """Inventory matches if any exist; otherwise slug guesses on every platform."""
    matches = inventory.get(normalize_name(name), [])
    if matches:
        return list(dict.fromkeys(matches))
    return [
        Proposal(platform, slug, "slug_guess")
        for slug in slug_guesses(name)
        for platform in PLATFORMS
    ]
