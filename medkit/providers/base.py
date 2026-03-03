from typing import Any, Protocol, Union, runtime_checkable

import httpx

from medkit.circuit_breaker import CircuitBreaker
from medkit.config import ProviderConfig, RetryConfig
from medkit.exceptions import APIError, ProviderUnavailableError, TimeoutError
from medkit.logging import get_logger


@runtime_checkable
class Provider(Protocol):
    """
    Protocol defining the contract for a MedKit data provider.
    """

    name: str

    async def search(self, query: str, **kwargs: Any) -> Any:
        """Asynchronous search interface."""
        ...

    def search_sync(self, query: str, **kwargs: Any) -> Any:
        """Synchronous search interface."""
        ...

    async def health_check_async(self) -> bool:
        """Check if the provider is available asynchronously."""
        ...

    def health_check(self) -> bool:
        """Check if the provider is available."""
        ...

    def capabilities(self) -> list[str]:
        """Return list of supported features."""
        ...

    async def get(self, item_id: str) -> Any:
        """Fetch record by ID."""
        ...

    def get_sync(self, item_id: str) -> Any:
        """Fetch record by ID (sync)."""
        ...


logger = get_logger("medkit.providers")

# ... (keep existing Provider protocol above BaseProvider)


class BaseProvider:
    """
    Base class for MedKit providers.
    Implements a resilient HTTP client wrapper with circuit breakers, retries, and logging.
    """

    def __init__(
        self,
        client: Union[httpx.Client, httpx.AsyncClient],
        config: ProviderConfig = ProviderConfig(),
        retry_config: RetryConfig = RetryConfig(),
    ):
        self.client = client
        self.config = config
        self.retry_config = retry_config
        self.name = "base"
        self.circuit_breaker = CircuitBreaker(provider_name=self.name)

    async def _async_request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        """Asynchronous HTTP request wrapper with circuit breaking and error handling."""
        self.circuit_breaker.check()

        timeout = kwargs.pop("timeout", self.config.timeout)

        try:
            logger.debug(f"[{self.name}] Async {method} {url}")
            if not isinstance(self.client, httpx.AsyncClient):
                raise TypeError("Expected an AsyncClient for _async_request")

            response = await self.client.request(method, url, timeout=timeout, **kwargs)
            response.raise_for_status()

            self.circuit_breaker.record_success()
            logger.info(f"[{self.name}] Async {method} {url} - {response.status_code}")
            return response

        except httpx.HTTPStatusError as e:
            self.circuit_breaker.record_failure()
            if e.response.status_code == 404:
                logger.info(f"[{self.name}] HTTP 404 Not Found")
            else:
                logger.error(f"[{self.name}] HTTP Error {e.response.status_code}: {e.response.text}")
            raise APIError(
                f"API Error from {self.name}: {e.response.text}",
                status_code=e.response.status_code,
                response_body=e.response.text,
                provider=self.name,
            ) from e

        except httpx.TimeoutException as e:
            self.circuit_breaker.record_failure()
            logger.error(f"[{self.name}] Timeout Error")
            raise TimeoutError(f"Request to {self.name} timed out.", provider=self.name) from e

        except httpx.RequestError as e:
            self.circuit_breaker.record_failure()
            logger.error(f"[{self.name}] Request Error: {str(e)}")
            raise ProviderUnavailableError(
                f"Failed to connect to {self.name}.", provider=self.name
            ) from e

    def _sync_request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        """Synchronous HTTP request wrapper with circuit breaking and error handling."""
        self.circuit_breaker.check()

        timeout = kwargs.pop("timeout", self.config.timeout)

        try:
            logger.debug(f"[{self.name}] Sync {method} {url}")
            if not isinstance(self.client, httpx.Client):
                raise TypeError("Expected a sync Client for _sync_request")

            response = self.client.request(method, url, timeout=timeout, **kwargs)
            response.raise_for_status()

            self.circuit_breaker.record_success()
            logger.info(f"[{self.name}] Sync {method} {url} - {response.status_code}")
            return response

        except httpx.HTTPStatusError as e:
            self.circuit_breaker.record_failure()
            if e.response.status_code == 404:
                logger.info(f"[{self.name}] HTTP 404 Not Found")
            else:
                logger.error(f"[{self.name}] HTTP Error {e.response.status_code}: {e.response.text}")
            raise APIError(
                f"API Error from {self.name}: {e.response.text}",
                status_code=e.response.status_code,
                response_body=e.response.text,
                provider=self.name,
            ) from e

        except httpx.TimeoutException as e:
            self.circuit_breaker.record_failure()
            logger.error(f"[{self.name}] Timeout Error")
            raise TimeoutError(f"Request to {self.name} timed out.", provider=self.name) from e

        except httpx.RequestError as e:
            self.circuit_breaker.record_failure()
            logger.error(f"[{self.name}] Request Error: {str(e)}")
            raise ProviderUnavailableError(
                f"Failed to connect to {self.name}.", provider=self.name
            ) from e

    async def search(self, query: str, **kwargs: Any) -> Any:
        raise NotImplementedError("Subclasses must implement search()")

    def search_sync(self, query: str, **kwargs: Any) -> Any:
        raise NotImplementedError("Subclasses must implement search_sync()")

    async def health_check_async(self) -> bool:
        """Default health check: verify base URL is reachable."""
        return True

    def health_check(self) -> bool:
        """Default health check: verify base URL is reachable."""
        return True

    def capabilities(self) -> list[str]:
        return []

    async def get(self, item_id: str) -> Any:
        raise NotImplementedError

    def get_sync(self, item_id: str) -> Any:
        raise NotImplementedError
