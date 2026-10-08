import pytest

from hiring_pipeline.companies import (
    Proposal,
    load_inventory,
    normalize_name,
    propose_boards,
    slug_guesses,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Airbnb, Inc.", "airbnb"),
        ("Alphabet Inc. (Class A)", "alphabet"),
        ("Palantir Technologies", "palantir"),
        ("Johnson & Johnson", "johnson and johnson"),
        ("Moody's Corporation", "moodys"),
        ("Société Générale", "societe generale"),
        ("  Scale   AI ", "scale ai"),
    ],
)
def test_normalize_name(raw, expected):
    assert normalize_name(raw) == expected


def test_slug_guesses_multi_word():
    assert slug_guesses("Scale AI") == ["scaleai", "scale-ai", "scale", "scaleaihq"]


def test_slug_guesses_drops_duplicates():
    assert slug_guesses("Palantir Technologies") == ["palantir", "palantirhq"]


def test_slug_guesses_empty_name():
    assert slug_guesses("Inc.") == []


@pytest.fixture
def inventory(tmp_path):
    path = tmp_path / "companies.csv"
    path.write_text(
        "ats,name,slug,url\n"
        "greenhouse,Airbnb,airbnb,https://example.com\n"
        "lever,Palantir Technologies,palantir,https://example.com\n"
        "ashby,Acme,acme,https://example.com\n"
        "greenhouse,Acme Inc.,acmeinc,https://example.com\n"
        "workday,Big Corp,bigcorp,https://example.com\n",
        encoding="utf-8",
    )
    return load_inventory(path)


def test_load_inventory_skips_unsupported_platforms(inventory):
    assert "big" not in inventory
    assert len(inventory) == 3


def test_inventory_match_is_used_without_guesses(inventory):
    assert propose_boards("Airbnb, Inc.", inventory) == [
        Proposal("greenhouse", "airbnb", "inventory")
    ]


def test_all_inventory_matches_are_returned(inventory):
    assert propose_boards("ACME", inventory) == [
        Proposal("ashby", "acme", "inventory"),
        Proposal("greenhouse", "acmeinc", "inventory"),
    ]


def test_no_inventory_match_falls_back_to_guesses(inventory):
    proposals = propose_boards("Notion Labs", inventory)
    assert {p.match_method for p in proposals} == {"slug_guess"}
    assert proposals[:3] == [
        Proposal("greenhouse", "notion", "slug_guess"),
        Proposal("lever", "notion", "slug_guess"),
        Proposal("ashby", "notion", "slug_guess"),
    ]
