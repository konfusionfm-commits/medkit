from __future__ import annotations

from typing import Any, Dict, Optional, Union


class MedKitError(Exception):
    """Base exception for MedKit SDK."""

    def __init__(
        self,
        message: str,
        *,
        provider: Optional[str] = None,
        request_id: Optional[str] = None,
    ):
        self.provider = provider
        self.request_id = request_id
        super().__init__(message)


class ConfigurationError(MedKitError):
    """Raised when the SDK is improperly configured."""

    pass


class ValidationError(MedKitError):
    """Raised when input parameters fail validation before hitting the API."""

    pass


class APIError(MedKitError):
    """Raised when an external API returns an error."""

    def __init__(
        self,
        message: str,
        *,
        status_code: Optional[int] = None,
        response_body: Optional[Union[str, Dict[str, Any]]] = None,
        provider: Optional[str] = None,
        request_id: Optional[str] = None,
    ):
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(message, provider=provider, request_id=request_id)


class RateLimitError(APIError):
    """Raised when an API rate limit is exceeded."""

    def __init__(
        self,
        message: str,
        *,
        retry_after: Optional[float] = None,
        status_code: Optional[int] = None,
        response_body: Optional[Union[str, Dict[str, Any]]] = None,
        provider: Optional[str] = None,
        request_id: Optional[str] = None,
    ):
        self.retry_after = retry_after
        super().__init__(
            message,
            status_code=status_code,
            response_body=response_body,
            provider=provider,
            request_id=request_id,
        )


class TimeoutError(APIError):
    """Raised when an API request times out."""

    pass


class AuthenticationError(APIError):
    """Raised when API credentials are invalid or missing."""

    pass


class NotFoundError(APIError):
    """Raised when a requested resource is not found."""

    pass


class ProviderUnavailableError(APIError):
    """Raised when a specific provider is down."""

    pass


class CircuitOpenError(MedKitError):
    """Raised when the circuit breaker is OPEN for a provider."""

    pass


class InvalidQueryError(MedKitError):
    """Raised when a query is malformed or invalid."""

    pass


class PluginError(MedKitError):
    """Raised when there is an issue with a provider plugin."""

    pass
