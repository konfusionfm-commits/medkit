from __future__ import annotations

import os
from typing import Any, Dict, Literal, Optional, Tuple, Type

from pydantic import BaseModel, ConfigDict, Field

from medkit.exceptions import APIError, TimeoutError


class RetryConfig(BaseModel):
    max_retries: int = Field(default=3, ge=0)
    base_delay: float = Field(default=0.5, gt=0)
    max_delay: float = Field(default=30.0, gt=0)
    jitter: Literal["full", "equal", "decorrelated", "none"] = "full"
    # Note: retry_on is hard to validate nicely in Pydantic, so we use a simple type
    # By default we retry on API errors (like 500s) and Timeouts.
    retry_on: Tuple[Type[Exception], ...] = Field(default=(APIError, TimeoutError))

    model_config = ConfigDict(arbitrary_types_allowed=True)


class ProviderConfig(BaseModel):
    """Configuration for an individual provider."""

    timeout: Optional[float] = None
    rate_limit: Optional[int] = None
    api_key: Optional[str] = None


class MedKitConfig(BaseModel):
    """Central configuration for the MedKit SDK."""

    timeout: float = 10.0
    max_connections: int = 100
    max_keepalive_connections: int = 20
    keepalive_expiry: float = 5.0
    http2: bool = False
    enable_compression: bool = True
    cache_backend: Literal["memory", "disk", "none"] = "memory"
    cache_ttl: int = 3600
    log_level: str = "WARNING"
    retry: RetryConfig = Field(default_factory=lambda: RetryConfig())
    providers: Dict[str, ProviderConfig] = Field(default_factory=dict)

    @classmethod
    def from_env(cls) -> MedKitConfig:
        """Load configuration from environment variables."""
        config_data: dict[str, Any] = {}

        # Basic settings
        if "MEDKIT_TIMEOUT" in os.environ:
            config_data["timeout"] = float(os.environ["MEDKIT_TIMEOUT"])
        if "MEDKIT_MAX_CONNECTIONS" in os.environ:
            config_data["max_connections"] = int(os.environ["MEDKIT_MAX_CONNECTIONS"])
        if "MEDKIT_CACHE_BACKEND" in os.environ:
            config_data["cache_backend"] = os.environ["MEDKIT_CACHE_BACKEND"]
        if "MEDKIT_CACHE_TTL" in os.environ:
            config_data["cache_ttl"] = int(os.environ["MEDKIT_CACHE_TTL"])
        if "MEDKIT_LOG_LEVEL" in os.environ:
            config_data["log_level"] = os.environ["MEDKIT_LOG_LEVEL"]

        # Retry config
        retry_data: dict[str, Any] = {}
        if "MEDKIT_RETRY_MAX" in os.environ:
            retry_data["max_retries"] = int(os.environ["MEDKIT_RETRY_MAX"])
        if "MEDKIT_RETRY_DELAY" in os.environ:
            retry_data["base_delay"] = float(os.environ["MEDKIT_RETRY_DELAY"])
        if "MEDKIT_RETRY_JITTER" in os.environ:
            retry_data["jitter"] = os.environ["MEDKIT_RETRY_JITTER"]

        if retry_data:
            config_data["retry"] = RetryConfig(**retry_data)

        # Provider configs
        providers: dict[str, ProviderConfig] = {}
        provider_names = ["OPENFDA", "PUBMED", "CLINICALTRIALS"]
        for p in provider_names:
            p_lower = p.lower()
            p_data: dict[str, Any] = {}
            if f"MEDKIT_{p}_TIMEOUT" in os.environ:
                p_data["timeout"] = float(os.environ[f"MEDKIT_{p}_TIMEOUT"])
            if f"MEDKIT_{p}_API_KEY" in os.environ:
                p_data["api_key"] = os.environ[f"MEDKIT_{p}_API_KEY"]
            if f"MEDKIT_{p}_RATE_LIMIT" in os.environ:
                p_data["rate_limit"] = int(os.environ[f"MEDKIT_{p}_RATE_LIMIT"])

            if p_data:
                providers[p_lower] = ProviderConfig(**p_data)

        if providers:
            config_data["providers"] = providers

        return cls(**config_data)
