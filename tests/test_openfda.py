from unittest.mock import AsyncMock, patch

import httpx
import pytest

from medkit.providers.openfda import OpenFDAProvider


@pytest.fixture
def test_client():
    return httpx.AsyncClient()


@pytest.fixture
def test_provider(test_client):
    return OpenFDAProvider(client=test_client)


@pytest.mark.asyncio
async def test_openfda_health_check(test_provider):
    with patch.object(test_provider.client, "get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value.status_code = 200
        assert await test_provider.health_check_async() is True

        mock_get.return_value.status_code = 500
        assert await test_provider.health_check_async() is False


@pytest.mark.asyncio
async def test_openfda_search_returns_empty_list_on_404(test_provider):
    with patch.object(test_provider, "_async_request", new_callable=AsyncMock) as mock_req:
        from medkit.exceptions import APIError

        # Simulate OpenFDA 404
        mock_req.side_effect = APIError("Not found", status_code=404)

        results = await test_provider.search("random_nonexistent_drug")
        assert results == []


@pytest.mark.asyncio
async def test_openfda_search_success(test_provider):
    with patch.object(test_provider, "_async_request", new_callable=AsyncMock) as mock_req:
        import httpx

        # Mock actual openFDA response
        mock_response = httpx.Response(
            200,
            json={
                "results": [
                    {
                        "openfda": {
                            "brand_name": ["Aspirin"],
                            "generic_name": ["Aspirin"],
                            "manufacturer_name": ["Bayer"],
                        },
                        "indications_and_usage": ["Pain"],
                        "warnings": ["Bleeding risk"],
                    }
                ]
            },
        )
        # Important: set the mock's request attribute to avoid errors
        mock_response._request = httpx.Request("GET", "https://api.fda.gov")
        mock_req.return_value = mock_response

        results = await test_provider.search("aspirin_mock_test")
        assert len(results) == 1
        assert results[0].brand_name == "Aspirin"
        assert results[0].generic_name == "Aspirin"
        assert results[0].manufacturer == "Bayer"
        assert results[0].indications == ["Pain"]
