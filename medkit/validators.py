from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict, Field

from medkit.exceptions import ValidationError

__all__ = ["sanitize_query", "BaseRequestValidator", "DrugSearchQuery", "PubMedSearchQuery"]


class BaseRequestValidator(BaseModel):
    """Base Pydantic model for validating API request parameters."""

    model_config = ConfigDict(extra="ignore", arbitrary_types_allowed=True)


class DrugSearchQuery(BaseRequestValidator):
    name: str = Field(min_length=1)


class PubMedSearchQuery(BaseRequestValidator):
    term: str = Field(min_length=1)
    limit: int = Field(default=10, le=100)


def sanitize_query(query: str) -> str:
    """
    Sanitize a search query to prevent injection and malformed requests.
    Strips dangerous characters while preserving legitimate medical terms
    (which can include hyphens, commas, etc.).
    """
    if not query or not str(query).strip():
        raise ValidationError("Query cannot be empty.")

    query = str(query).strip()

    if len(query) > 200:
        raise ValidationError("Query exceeds maximum allowed length of 200 characters.")

    # Remove characters that might break upstream API parsing (HTML tags, non-printable)
    # Allows alphanumerics, spaces, hyphens, underscores, commas, periods
    sanitized = re.sub(r"[^\w\s\-\.,]", "", query)

    # Normalize excessive whitespace
    sanitized = re.sub(r"\s+", " ", sanitized)

    if not sanitized.strip():
        raise ValidationError("Query contains no valid search characters after sanitization.")

    return sanitized


def validate_nct_id(nct_id: str) -> str:
    """Validates a ClinicalTrials.gov NCT Identifier (e.g., NCT00000105)."""
    nct_id = str(nct_id).strip().upper()
    if not re.match(r"^NCT\d{8}$", nct_id):
        raise ValidationError(
            f"Invalid NCT ID format: '{nct_id}'. Expected format 'NCT' followed by 8 digits."
        )
    return nct_id


def validate_pmid(pmid: str) -> str:
    """Validates a PubMed ID (numeric string)."""
    pmid = str(pmid).strip()
    if not re.match(r"^[1-9]\d{0,8}$", pmid):
        raise ValidationError(f"Invalid PubMed ID format: '{pmid}'. Expected 1-9 digits.")
    return pmid
