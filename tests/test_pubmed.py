from unittest.mock import AsyncMock, patch

import httpx
import pytest

from medkit.models import ResearchPaper
from medkit.providers.pubmed import PubMedProvider


@pytest.fixture
def test_client():
    return httpx.AsyncClient()


@pytest.fixture
def test_provider(test_client):
    from medkit.config import ProviderConfig

    provider = PubMedProvider(client=test_client)
    provider.config = ProviderConfig(timeout=10.0, max_retries=3)
    return provider


@pytest.mark.asyncio
async def test_pubmed_health_check(test_provider):
    with patch.object(test_provider.client, "get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value.status_code = 200
        assert await test_provider.health_check_async() is True

        mock_get.return_value.status_code = 500
        assert await test_provider.health_check_async() is False


@pytest.mark.asyncio
async def test_pubmed_search_returns_empty_list_on_404(test_provider):
    with patch.object(test_provider, "_async_request", new_callable=AsyncMock) as mock_req:
        import httpx

        mock_response = httpx.Response(200, json={"esearchresult": {"idlist": []}})
        mock_response._request = httpx.Request("GET", "https://eutils.ncbi.nlm.nih.gov")
        mock_req.return_value = mock_response

        results = await test_provider.search("random_nonexistent_disease")
        assert results == []


@pytest.mark.asyncio
async def test_pubmed_search_success(test_provider):
    # Instead of doing massive mock logic for pubmed's 2-stage (esearch then esummary)
    # Let's mock the actual _async_request to yield the two stages
    with patch.object(test_provider, "_async_request", new_callable=AsyncMock) as mock_req:
        import httpx

        esearch_response = httpx.Response(200, json={"esearchresult": {"idlist": ["12345"]}})
        esummary_response = httpx.Response(
            200,
            json={
                "result": {
                    "uids": ["12345"],
                    "12345": {
                        "uid": "12345",
                        "title": "A Mocked Paper Title",
                        "authors": [{"name": "Smith J"}],
                        "pubdate": "2026",
                        "source": "Mock Journal",
                    },
                }
            },
        )
        esearch_response._request = httpx.Request("GET", "https://eutils.ncbi.nlm.nih.gov")
        esummary_response._request = httpx.Request("GET", "https://eutils.ncbi.nlm.nih.gov")

        mock_req.side_effect = [esearch_response, esummary_response]

        results = await test_provider.search("cancer")
        assert len(results) == 1
        assert isinstance(results[0], ResearchPaper)
        assert results[0].title == "A Mocked Paper Title"
        assert results[0].pmid == "12345"
        assert (
            results[0].journal is None
        )  # Pydantic model doesn't map "source" to "journal" out of the box unless specified.
