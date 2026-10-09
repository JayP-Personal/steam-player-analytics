import pytest
import requests
import responses

from hiring_pipeline.companies import Proposal
from hiring_pipeline.verification import (
    ENDPOINTS,
    BoardCheck,
    check_board,
    names_match,
    postings_in,
    verify_company,
)

GH_URL = ENDPOINTS["greenhouse"].format(slug="acme")
LEVER_URL = ENDPOINTS["lever"].format(slug="acme")


# --- parsing -------------------------------------------------------------


def test_postings_in_handles_each_platform_shape():
    assert postings_in("greenhouse", {"jobs": [{"title": "A"}]}) == [{"title": "A"}]
    assert postings_in("ashby", {"jobs": [{"title": "B"}]}) == [{"title": "B"}]
    assert postings_in("lever", [{"text": "C"}]) == [{"text": "C"}]


def test_postings_in_tolerates_unexpected_payloads():
    assert postings_in("lever", {"ok": False}) == []
    assert postings_in("greenhouse", []) == []


@pytest.mark.parametrize(
    ("candidate", "board_company", "expected"),
    [
        ("Airbnb, Inc.", "Airbnb", True),
        ("Scale AI", "Scale AI, Inc.", True),
        ("Notion Labs", "Notion", True),
        ("Acme", "Globex", False),
        ("Acme", None, False),
    ],
)
def test_names_match(candidate, board_company, expected):
    assert names_match(candidate, board_company) is expected


# --- live checks (HTTP mocked with `responses`) --------------------------


@pytest.fixture
def session():
    return requests.Session()


@responses.activate
def test_check_board_reads_greenhouse_postings(session):
    jobs = [{"title": "Data Engineer", "company_name": "Acme"}, {"title": "Analyst"}]
    responses.get(GH_URL, json={"jobs": jobs})
    check = check_board(session, "greenhouse", "acme")
    assert check == BoardCheck(True, False, 2, "Acme", ("Data Engineer", "Analyst"))


@responses.activate
def test_check_board_404_is_not_an_error(session):
    responses.get(LEVER_URL, status=404, json={"ok": False})
    assert check_board(session, "lever", "acme") == BoardCheck(False, False)


@responses.activate
def test_check_board_server_error_is_an_error(session):
    responses.get(LEVER_URL, status=500)
    assert check_board(session, "lever", "acme").error


# --- choosing a board ----------------------------------------------------


def fake_checker(results):
    """Return a checker that answers from a dict of (platform, slug) -> BoardCheck."""
    return lambda platform, slug: results.get(
        (platform, slug), BoardCheck(False, False)
    )


def test_first_board_with_postings_wins():
    proposals = [
        Proposal("greenhouse", "acme", "slug_guess"),
        Proposal("ashby", "acme", "slug_guess"),
    ]
    checker = fake_checker(
        {
            ("greenhouse", "acme"): BoardCheck(True, False, 0),  # exists but empty
            ("ashby", "acme"): BoardCheck(True, False, 5),
        }
    )
    result = verify_company("Acme", proposals, checker)
    assert result.proposal == proposals[1]


def test_inventory_match_is_verified():
    proposals = [Proposal("lever", "acme", "inventory")]
    checker = fake_checker({("lever", "acme"): BoardCheck(True, False, 3)})
    assert verify_company("Acme", proposals, checker).status == "verified"


def test_guess_confirmed_by_company_name_is_verified():
    proposals = [Proposal("greenhouse", "acme", "slug_guess")]
    checker = fake_checker(
        {("greenhouse", "acme"): BoardCheck(True, False, 3, "Acme Inc.")}
    )
    assert verify_company("Acme", proposals, checker).status == "verified"


def test_unconfirmed_guess_needs_review():
    proposals = [Proposal("ashby", "acme", "slug_guess")]
    checker = fake_checker({("ashby", "acme"): BoardCheck(True, False, 3)})
    assert verify_company("Acme", proposals, checker).status == "needs_review"


def test_no_board_found():
    proposals = [Proposal("lever", "acme", "slug_guess")]
    assert verify_company("Acme", proposals, fake_checker({})).status == "not_found"


def test_errors_are_reported_instead_of_not_found():
    proposals = [Proposal("lever", "acme", "slug_guess")]
    checker = fake_checker({("lever", "acme"): BoardCheck(False, True)})
    assert verify_company("Acme", proposals, checker).status == "error"
