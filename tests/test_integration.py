from unittest.mock import AsyncMock, patch

import httpx
import pytest

from medkit.client import AsyncMedKit
from medkit.models import SearchResults


@pytest.fixture
def mock_openfda():
    response = httpx.Response(
        200,
        json={
            "results": [
                {"openfda": {"brand_name": ["Aspirin"]}, "indications_and_usage": ["Pain Relief"]}
            ]
        },
    )
    response._request = httpx.Request("GET", "https://api.fda.gov")
    return response


@pytest.fixture
def mock_pubmed_esearch():
    response = httpx.Response(200, json={"esearchresult": {"idlist": ["111"]}})
    response._request = httpx.Request("GET", "https://eutils.ncbi.nlm.nih.gov")
    return response


@pytest.fixture
def mock_pubmed_esummary():
    response = httpx.Response(
        200, json={"result": {"uids": ["111"], "111": {"uid": "111", "title": "Paper Title"}}}
    )
    response._request = httpx.Request("GET", "https://eutils.ncbi.nlm.nih.gov")
    return response


@pytest.fixture
def mock_trials():
    response = httpx.Response(
        200,
        json={
            "studies": [
                {
                    "protocolSection": {
                        "identificationModule": {"nctId": "NCT111", "briefTitle": "Trial Title"},
                        "statusModule": {"overallStatus": "RECRUITING"},
                    }
                }
            ]
        },
    )
    response._request = httpx.Request("GET", "https://clinicaltrials.gov")
    return response


@pytest.mark.asyncio
async def test_integration_full_search(
    mock_openfda, mock_pubmed_esearch, mock_pubmed_esummary, mock_trials
):
    async with AsyncMedKit() as med:
        # Patch the base HTTP async clients
        with patch.object(
            med._providers["openfda"].client, "get", new_callable=AsyncMock
        ) as get_fda:
            with patch.object(
                med._providers["pubmed"], "_async_request", new_callable=AsyncMock
            ) as req_pub:
                with patch.object(
                    med._providers["clinicaltrials"].client, "get", new_callable=AsyncMock
                ) as get_trials:
                    get_fda.return_value = mock_openfda
                    get_trials.return_value = mock_trials
                    req_pub.side_effect = [mock_pubmed_esearch, mock_pubmed_esummary]

                    # Prevent pubmed limiter from sleeping unnecessarily in tests
                    with patch("asyncio.sleep", new_callable=AsyncMock):
                        results = await med.search("aspirin")

                        assert isinstance(results, SearchResults)
                        assert len(results.drugs) == 1
                        assert results.drugs[0].brand_name == "Low Dose Aspirin"

                        assert len(results.papers) >= 1
                        assert results.papers[0].title == "Paper Title"

                        assert len(results.trials) >= 1
                        assert results.trials[0].title is not None

                        assert results.metadata.sources == ["openfda", "pubmed", "clinicaltrials"]
