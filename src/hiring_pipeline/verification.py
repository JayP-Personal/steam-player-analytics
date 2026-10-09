"""Check proposed job boards against the live platform APIs.

For each company, proposals are tried in order and the first board with at
least one open posting is kept.
"""

from __future__ import annotations

from dataclasses import dataclass

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from hiring_pipeline.companies import Proposal, normalize_name

ENDPOINTS = {
    "greenhouse": "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs",
    "lever": "https://api.lever.co/v0/postings/{slug}?mode=json",
    "ashby": "https://api.ashbyhq.com/posting-api/job-board/{slug}",
}
USER_AGENT = "tech-hiring-signals (portfolio research project)"


@dataclass(frozen=True)
class BoardCheck:
    """What the live API returned for one board."""

    found: bool  # board exists (any 2xx response)
    error: bool  # request failed for a reason other than "no such board"
    postings: int = 0
    board_company: str | None = None  # company name the API reports, if any
    sample_titles: tuple[str, ...] = ()


@dataclass(frozen=True)
class Verification:
    """Outcome for one candidate company."""

    status: str  # verified | needs_review | not_found | error
    proposal: Proposal | None = None
    check: BoardCheck | None = None


def make_session() -> requests.Session:
    """HTTP session that retries rate limits and server errors with backoff."""
    retry = Retry(
        total=3,
        backoff_factor=2,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
    )
    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session


def postings_in(platform: str, payload: object) -> list[dict]:
    """Extract the list of postings; each platform nests it differently."""
    if platform == "lever":
        jobs = payload if isinstance(payload, list) else []
    else:
        jobs = payload.get("jobs", []) if isinstance(payload, dict) else []
    return [job for job in jobs if isinstance(job, dict)]


def title_of(platform: str, posting: dict) -> str:
    return str(posting.get("text" if platform == "lever" else "title", ""))


def check_board(session: requests.Session, platform: str, slug: str) -> BoardCheck:
    url = ENDPOINTS[platform].format(slug=slug)
    try:
        response = session.get(url, timeout=20)
    except requests.RequestException:
        return BoardCheck(found=False, error=True)
    if response.status_code == 404:
        return BoardCheck(found=False, error=False)
    if not response.ok:
        return BoardCheck(found=False, error=True)
    try:
        jobs = postings_in(platform, response.json())
    except ValueError:  # not JSON
        return BoardCheck(found=False, error=True)

    # Greenhouse is the only platform that names the company on each posting.
    company = jobs[0].get("company_name") if jobs and platform == "greenhouse" else None
    titles = tuple(title_of(platform, job) for job in jobs[:3])
    return BoardCheck(True, False, len(jobs), company, titles)


def names_match(candidate: str, board_company: str | None) -> bool:
    if not board_company:
        return False
    a, b = normalize_name(candidate), normalize_name(board_company)
    return bool(a and b) and (a == b or a in b or b in a)


def verify_company(candidate: str, proposals: list[Proposal], checker) -> Verification:
    """Try proposals in order; keep the first board with open postings.

    `checker(platform, slug)` returns a BoardCheck. It's passed in so this
    logic can be tested without network calls.
    """
    had_error = False
    for proposal in proposals:
        check = checker(proposal.platform, proposal.board_slug)
        had_error |= check.error
        if check.postings == 0:
            continue
        confirmed = proposal.match_method == "inventory" or names_match(
            candidate, check.board_company
        )
        status = "verified" if confirmed else "needs_review"
        return Verification(status, proposal, check)
    return Verification("error" if had_error else "not_found")
