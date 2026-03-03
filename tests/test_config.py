import pytest
from pydantic import ValidationError

from medkit.config import MedKitConfig


def test_config_defaults():
    config = MedKitConfig()
    assert config.timeout == 10.0
    assert config.max_connections == 100
    assert config.cache_backend == "memory"
    assert config.retry.max_retries == 3
    assert config.retry.base_delay == 0.5


def test_config_from_env(monkeypatch):
    monkeypatch.setenv("MEDKIT_TIMEOUT", "5.0")
    monkeypatch.setenv("MEDKIT_CACHE_BACKEND", "disk")
    monkeypatch.setenv("MEDKIT_RETRY_MAX", "5")
    monkeypatch.setenv("MEDKIT_OPENFDA_TIMEOUT", "15.0")

    config = MedKitConfig.from_env()
    assert config.timeout == 5.0
    assert config.cache_backend == "disk"
    assert config.retry.max_retries == 5

    # Provider config parsed
    assert "openfda" in config.providers
    assert config.providers["openfda"].timeout == 15.0


def test_config_validation_errors():
    with pytest.raises(ValidationError):
        # Pass a completely wrong type that cannot be coerced
        MedKitConfig(timeout="invalid string")

    with pytest.raises(ValidationError):
        MedKitConfig(cache_backend="unsupported_backend")  # Literal
