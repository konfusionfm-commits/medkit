from __future__ import annotations

from typing import Any, Dict, List, cast

import httpx

from ..exceptions import APIError, NotFoundError
from ..models import ResearchPaper
from .base import BaseProvider


class PubMedProvider(BaseProvider):
    """
    Provider for PubMed (NCBI Entrez) API.
    Handles publication search and retrieval.
    """

    def __init__(self, client: httpx.Client | httpx.AsyncClient):
        super().__init__(client)
        self.name = "pubmed"
        self.search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        self.summary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"

    async def health_check_async(self) -> bool:
        """Check if PubMed API is reachable asynchronously."""
        async_client = cast(httpx.AsyncClient, self.client)
        try:
            resp = await async_client.get(
                self.search_url,
                params={"db": "pubmed", "term": "test", "retmax": 1},
                timeout=2.0,
            )
            return resp.status_code == 200
        except Exception:
            return False

    def health_check(self) -> bool:
        """Check if PubMed API is reachable synchronously."""
        if not isinstance(self.client, httpx.Client):
            return True
        try:
            resp = self.client.get(
                self.search_url,
                params={"db": "pubmed", "term": "test", "retmax": 1},
                timeout=2.0,
            )
            return resp.status_code == 200
        except Exception:
            return False

    def capabilities(self) -> List[str]:
        return ["papers", "publications", "literature"]

    def _parse_summaries(self, data: Dict[str, Any], pmids: List[str]) -> List[ResearchPaper]:
        """Parse PubMed API results into ResearchPaper models."""
        results = data.get("result", {})
        papers = []

        for pmid in pmids:
            paper_data = results.get(pmid, {})
            if not paper_data or "error" in paper_data:
                continue

            title = paper_data.get("title", "Untitled Publication")
            authors = [
                str(author.get("name"))
                for author in paper_data.get("authors", [])
                if author.get("name")
            ]
            journal = paper_data.get("fulljournalname")

            pubdate = paper_data.get("pubdate", "")
            year = None
            if pubdate:
                # Often '2023 May 1' or just '2023'
                year_match = pubdate.split(" ")[0]
                if year_match.isdigit():
                    year = int(year_match)

            try:
                papers.append(
                    ResearchPaper(
                        pmid=pmid,
                        title=title,
                        authors=authors,
                        journal=journal,
                        year=year,
                        abstract=None,
                        url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                    )
                )
            except Exception:
                continue
        return papers

    def get_sync(self, item_id: str) -> ResearchPaper:
        """Retrieve a single research paper by PMID synchronously."""
        from ..validators import validate_pmid

        item_id = validate_pmid(item_id)

        url = f"{self.summary_url}?db=pubmed&id={item_id}&retmode=json"

        try:
            response = self._sync_request("GET", url)
            results = self._parse_summaries(response.json(), [item_id])
            if not results:
                raise NotFoundError(f"PMID {item_id} not found in PubMed.", provider=self.name)
            return results[0]
        except Exception as e:
            if not isinstance(e, (APIError, NotFoundError)):
                raise APIError(str(e), provider=self.name) from e
            raise

    async def get(self, item_id: str) -> ResearchPaper:
        """Retrieve a single research paper by PMID asynchronously."""
        from ..validators import validate_pmid

        item_id = validate_pmid(item_id)

        url = f"{self.summary_url}?db=pubmed&id={item_id}&retmode=json"

        try:
            response = await self._async_request("GET", url)
            results = self._parse_summaries(response.json(), [item_id])
            if not results:
                raise NotFoundError(f"PMID {item_id} not found in PubMed.", provider=self.name)
            return results[0]
        except Exception as e:
            if not isinstance(e, (APIError, NotFoundError)):
                raise APIError(str(e), provider=self.name) from e
            raise

    def search_sync(self, query: str, limit: int = 10, **kwargs: Any) -> list[ResearchPaper]:
        """Search for research papers synchronously."""
        from ..validators import sanitize_query

        query = sanitize_query(query)

        search_url = f"{self.search_url}?db=pubmed&term={query}&retmode=json&retmax={limit}"

        try:
            # Step 1: Search for IDs
            search_res = self._sync_request("GET", search_url)
            pmids = search_res.json().get("esearchresult", {}).get("idlist", [])

            if not pmids:
                return []

            # Step 2: Get summaries
            pmids_str = ",".join(pmids)
            summary_url = f"{self.summary_url}?db=pubmed&id={pmids_str}&retmode=json"

            summary_res = self._sync_request("GET", summary_url)
            return self._parse_summaries(summary_res.json(), pmids)

        except httpx.HTTPError as e:
            raise APIError(f"Failed to fetch data from PubMed: {e}", provider=self.name) from e

    async def search(self, query: str, **kwargs: Any) -> List[ResearchPaper]:
        """Search for research papers asynchronously."""
        from ..validators import sanitize_query

        query = sanitize_query(query)
        limit = kwargs.get("limit", 10)

        search_url = f"{self.search_url}?db=pubmed&term={query}&retmode=json&retmax={limit}"

        try:
            # Step 1: Search for IDs
            search_res = await self._async_request("GET", search_url)
            pmids = search_res.json().get("esearchresult", {}).get("idlist", [])

            if not pmids:
                return []

            # Step 2: Get summaries
            pmids_str = ",".join(pmids)
            summary_url = f"{self.summary_url}?db=pubmed&id={pmids_str}&retmode=json"

            summary_res = await self._async_request("GET", summary_url)
            return self._parse_summaries(summary_res.json(), pmids)

        except httpx.HTTPError as e:
            raise APIError(f"Failed to fetch data from PubMed: {e}", provider=self.name) from e
