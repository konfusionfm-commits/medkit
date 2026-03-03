import pytest

from medkit.validators import DrugSearchQuery, PubMedSearchQuery, sanitize_query


def test_sanitize_query():
    assert sanitize_query("aspirin") == "aspirin"
    assert sanitize_query("aspirin; drop tables;") == "aspirin drop tables"

    from medkit.exceptions import ValidationError

    with pytest.raises(ValidationError):
        sanitize_query("aspirin" * 100)


def test_sanitize_query_preserves_spaces():
    assert sanitize_query("lung cancer") == "lung cancer"


def test_drug_search_query_validation():
    query = DrugSearchQuery(name="aspirin")
    assert query.name == "aspirin"

    with pytest.raises(ValueError):
        DrugSearchQuery(name="")  # Empty string


def test_pubmed_search_query_validation():
    query = PubMedSearchQuery(term="cancer", limit=10)
    assert query.term == "cancer"
    assert query.limit == 10

    with pytest.raises(ValueError):
        PubMedSearchQuery(term="cancer", limit=200)  # Exceeds max limit
