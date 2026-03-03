from __future__ import annotations

import asyncio
import json
import subprocess
from typing import Any, Dict, List, Optional, cast
from urllib.parse import urlencode

import httpx

from ..exceptions import APIError, NotFoundError
from ..models import ClinicalTrial
from .base import BaseProvider


class ClinicalTrialsProvider(BaseProvider):
    """
    Provider for ClinicalTrials.gov API.
    Handles searching and retrieving clinical studies with a curl fallback.
    """

    def __init__(self, client: httpx.Client | httpx.AsyncClient):
        super().__init__(client)
        self.name = "clinicaltrials"
        self.base_url = "https://clinicaltrials.gov/api/v2/studies"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

    def _curl_fetch(self, url: str, params: Optional[Dict[str, Any]] = None) -> str:
        """Fallback to system curl to bypass TLS fingerprinting blocks."""
        cmd = ["curl", "-s", "-L", "--connect-timeout", "10", "--compressed"]
        for k, v in self.headers.items():
            cmd.extend(["-H", f"{k}: {v}"])

        full_url = url
        if params:
            full_url = f"{url}?{urlencode(params)}"
        cmd.append(full_url)

        try:
            result = subprocess.run(cmd, capture_output=True, check=True)
            return result.stdout.decode("utf-8", errors="replace")
        except Exception:
            return ""

    def _parse_study(self, study: Dict[str, Any]) -> ClinicalTrial:
        """Parse raw study data into a ClinicalTrial model."""
        try:
            protocol = study.get("protocolSection", {})
            id_info = protocol.get("identificationModule", {})

            # Robust NCT ID extraction with whitespace stripping
            raw_nct = id_info.get("nctId", study.get("nctId", "NCT00000000"))
            nct_id = str(raw_nct).strip() if raw_nct else "NCT00000000"

            # Basic validation to avoid breaking Pydantic types if any
            if not nct_id.startswith("NCT") or len(nct_id) < 3:
                nct_id = "NCT00000000"

            status_info = protocol.get("statusModule", {})
            description_info = protocol.get("descriptionModule", {})
            conditions_info = protocol.get("conditionsModule", {})
            arms_info = protocol.get("armsInterventionsModule", {})
            design_info = protocol.get("designModule", {})
            eligibility_info = protocol.get("eligibilityModule", {})

            phases = cast(List[str], design_info.get("phases", []))

            # Filter for meaningful interventions (Drugs and Biologicals)
            relevant_types = ["DRUG", "BIOLOGICAL", "COMBINATION_PRODUCT"]
            interventions = [
                str(i.get("name", ""))
                for i in arms_info.get("interventions", [])
                if i.get("name") and (not i.get("type") or i.get("type").upper() in relevant_types)
            ]

            return ClinicalTrial(
                nct_id=nct_id,
                title=id_info.get("briefTitle", "N/A"),
                status=status_info.get("overallStatus", "UNKNOWN"),
                conditions=conditions_info.get("conditions", []),
                description=description_info.get("briefSummary", "N/A"),
                recruiting=status_info.get("overallStatus") in ["RECRUITING", "AVAILABLE"],
                url=f"https://clinicaltrials.gov/study/{nct_id}",
                phase=phases,
                location=[],
                eligibility=eligibility_info.get("eligibilityCriteria"),
                interventions=interventions,
            )
        except Exception:
            return ClinicalTrial(
                nct_id="NCT00000000",
                title="Unknown Study",
                status="UNKNOWN",
                conditions=[],
                description="Failed to parse details.",
                recruiting=False,
                url="https://clinicaltrials.gov/",
                phase=[],
                location=[],
                eligibility=None,
                interventions=[],
            )

    async def health_check_async(self) -> bool:
        # Check standard endpoint with a fast timeout
        try:
            client = cast(httpx.AsyncClient, self.client)
            resp = await client.get(self.base_url, params={"pageSize": 1}, timeout=2.0)
            resp.raise_for_status()
            return True
        except Exception:
            pass

        # Fallback to curl
        loop = asyncio.get_event_loop()
        res = await loop.run_in_executor(None, self._curl_fetch, self.base_url, {"pageSize": 1})
        return bool(res and '"studies"' in res)

    def health_check(self) -> bool:
        try:
            client = cast(httpx.Client, self.client)
            resp = client.get(self.base_url, params={"pageSize": 1}, timeout=2.0)
            resp.raise_for_status()
            return True
        except Exception:
            pass

        # Fallback to curl
        res = self._curl_fetch(self.base_url, {"pageSize": 1})
        return bool(res and '"studies"' in res)

    def capabilities(self) -> List[str]:
        return ["trials", "studies", "recruitment"]

    def search_sync(self, query: str, **kwargs: Any) -> List[ClinicalTrial]:
        from ..validators import sanitize_query

        query = sanitize_query(query)
        limit = kwargs.get("limit", 10)
        recruiting = kwargs.get("recruiting", False)

        params = {"pageSize": limit, "query.term": query}
        if recruiting:
            params["filter.overallStatus"] = "RECRUITING"

        try:
            url = f"{self.base_url}?{urlencode(params)}"
            client = cast(httpx.Client, self.client)
            response = client.get(url, timeout=self.config.timeout)
            response.raise_for_status()
            studies = response.json().get("studies", [])
            return [self._parse_study(s) for s in studies]
        except Exception as e:
            # Fallback to curl silently on TLS/Request issues
            res = self._curl_fetch(self.base_url, params)
            if res:
                try:
                    data = json.loads(res)
                    studies = data.get("studies", [])
                    return [self._parse_study(s) for s in studies]
                except Exception:
                    pass
            if not isinstance(e, (APIError, NotFoundError)):
                raise APIError(str(e), provider=self.name) from e
            raise

    async def search(self, query: str, **kwargs: Any) -> List[ClinicalTrial]:
        from ..validators import sanitize_query

        query = sanitize_query(query)
        limit = kwargs.get("limit", 10)
        recruiting = kwargs.get("recruiting", False)

        params = {"pageSize": limit, "query.term": query}
        if recruiting:
            params["filter.overallStatus"] = "RECRUITING"

        try:
            url = f"{self.base_url}?{urlencode(params)}"
            client = cast(httpx.AsyncClient, self.client)
            response = await client.get(url, timeout=self.config.timeout)
            response.raise_for_status()
            studies = response.json().get("studies", [])
            return [self._parse_study(s) for s in studies]
        except Exception as e:
            loop = asyncio.get_event_loop()
            res = await loop.run_in_executor(None, self._curl_fetch, self.base_url, params)
            if res:
                try:
                    data = json.loads(res)
                    studies = data.get("studies", [])
                    return [self._parse_study(s) for s in studies]
                except Exception:
                    pass
            if not isinstance(e, (APIError, NotFoundError)):
                raise APIError(str(e), provider=self.name) from e
            raise

    def get_sync(self, item_id: str) -> ClinicalTrial:
        from ..validators import validate_nct_id

        item_id = validate_nct_id(item_id)
        url = f"{self.base_url}/{item_id}"

        try:
            client = cast(httpx.Client, self.client)
            response = client.get(url, timeout=self.config.timeout)
            response.raise_for_status()
            return self._parse_study(response.json())
        except Exception as e:
            if (
                getattr(e, "status_code", None) == 404
                or getattr(getattr(e, "response", None), "status_code", None) == 404
            ):
                raise NotFoundError(f"Trial {item_id} not found.", provider=self.name)

            res = self._curl_fetch(url)
            if res:
                try:
                    return self._parse_study(json.loads(res))
                except Exception:
                    pass

            if not isinstance(e, (APIError, NotFoundError)):
                raise APIError(str(e), provider=self.name) from e
            raise

    async def get(self, item_id: str) -> ClinicalTrial:
        from ..validators import validate_nct_id

        item_id = validate_nct_id(item_id)
        url = f"{self.base_url}/{item_id}"

        try:
            client = cast(httpx.AsyncClient, self.client)
            response = await client.get(url, timeout=self.config.timeout)
            response.raise_for_status()
            return self._parse_study(response.json())
        except Exception as e:
            if getattr(e, "status_code", None) == 404:
                raise NotFoundError(f"Trial {item_id} not found.", provider=self.name)

            loop = asyncio.get_event_loop()
            res = await loop.run_in_executor(None, self._curl_fetch, url)
            if res:
                try:
                    return self._parse_study(json.loads(res))
                except Exception:
                    pass

            if not isinstance(e, (APIError, NotFoundError)):
                raise APIError(str(e), provider=self.name) from e
            raise
