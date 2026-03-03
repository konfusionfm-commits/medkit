import pytest

from medkit.config import RetryConfig
from medkit.exceptions import APIError
from medkit.retry import retry

test_config = RetryConfig(max_retries=3, base_delay=0.01)


class FlakyService:
    def __init__(self, fail_times=2):
        self.attempts = 0
        self.fail_times = fail_times

    @retry(config=test_config)
    def sync_call(self):
        self.attempts += 1
        if self.attempts <= self.fail_times:
            raise APIError("Failed")
        return "Success"

    @retry(config=test_config)
    async def async_call(self):
        self.attempts += 1
        if self.attempts <= self.fail_times:
            raise APIError("Failed")
        return "Success"


def test_sync_retry_success():
    service = FlakyService(fail_times=2)
    result = service.sync_call()
    assert result == "Success"
    assert service.attempts == 3


def test_sync_retry_failure():
    service = FlakyService(fail_times=5)
    with pytest.raises(APIError):
        service.sync_call()
    assert service.attempts == 4  # Initial + 3 retries


@pytest.mark.asyncio
async def test_async_retry_success():
    service = FlakyService(fail_times=2)
    result = await service.async_call()
    assert result == "Success"
    assert service.attempts == 3
