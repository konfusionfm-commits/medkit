from unittest.mock import AsyncMock, patch

import httpx
import pytest

from medkit.models import ClinicalTrial
from medkit.providers.clinicaltrials import ClinicalTrialsProvider


@pytest.fixture
def test_client():
    return httpx.AsyncClient()


@pytest.fixture
def test_provider(test_client):
    from medkit.config import ProviderConfig

    provider = ClinicalTrialsProvider(client=test_client)
    provider.config = ProviderConfig(timeout=10.0, max_retries=3)
    return provider


@pytest.mark.asyncio
async def test_clinicaltrials_health_check(test_provider):
    with patch.object(test_provider.client, "get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value.status_code = 200
        assert await test_provider.health_check_async() is True

        # Test fallback
        with patch.object(test_provider, "_curl_fetch", return_value='{"studies": []}'):
            mock_get.return_value.status_code = 500
            assert await test_provider.health_check_async() is True


@pytest.mark.asyncio
async def test_clinicaltrials_search_returns_empty_list_on_404(test_provider):
    with patch.object(test_provider.client, "get", new_callable=AsyncMock) as mock_req:
        # Simulate API Error
        mock_req.side_effect = Exception("Not found")

        # Must patch _curl_fetch too to ensure fallback payload represents an empty search
        with patch.object(test_provider, "_curl_fetch", return_value='{"studies": []}'):
            results = await test_provider.search("random_nonexistent_disease")
            assert results == []


@pytest.mark.asyncio
async def test_clinicaltrials_search_success(test_provider):
    with patch.object(test_provider.client, "get", new_callable=AsyncMock) as mock_req:
        import httpx

        mock_response = httpx.Response(
            200,
            json={
                "studies": [
                    {
                        "protocolSection": {
                            "identificationModule": {
                                "nctId": "NCT01234567",
                                "briefTitle": "Mock Trial",
                            },
                            "statusModule": {"overallStatus": "RECRUITING"},
                            "designModule": {"phases": ["PHASE2"]},
                            "descriptionModule": {"briefSummary": "Mock summary."},
                        }
                    }
                ]
            },
        )
        mock_response._request = httpx.Request("GET", "https://clinicaltrials.gov")
        mock_req.return_value = mock_response

        results = await test_provider.search("cancer")
        assert len(results) >= 1
        assert isinstance(results[0], ClinicalTrial)
        assert results[0].nct_id is not None
        assert results[0].status is not None
