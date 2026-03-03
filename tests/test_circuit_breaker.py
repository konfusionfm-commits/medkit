import time

import pytest

from medkit.circuit_breaker import CircuitBreaker, CircuitState
from medkit.exceptions import CircuitOpenError


def test_circuit_breaker_initial_state():
    cb = CircuitBreaker("test", failure_threshold=3)
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 0
    cb.check()  # Should not raise


def test_circuit_breaker_opens_on_failures():
    cb = CircuitBreaker("test", failure_threshold=3)
    cb.record_failure()
    cb.record_failure()
    assert cb.state == CircuitState.CLOSED
    cb.record_failure()
    assert cb.state == CircuitState.OPEN

    with pytest.raises(CircuitOpenError):
        cb.check()


def test_circuit_breaker_half_open_transition():
    cb = CircuitBreaker("test", failure_threshold=1, recovery_timeout=0.1)
    cb.record_failure()
    assert cb.state == CircuitState.OPEN

    with pytest.raises(CircuitOpenError):
        cb.check()

    time.sleep(0.15)

    # Needs to transition to HALF_OPEN and allow one request
    cb.check()
    assert cb.state == CircuitState.HALF_OPEN

    # We allow the test request but in our implementation, check() doesn't raise while half open
    cb.record_failure()  # Second request should fail while HALF_OPEN
    assert cb.state == CircuitState.OPEN

    # A success should reset it (need to be half open first)
    time.sleep(0.15)
    cb.check()  # Open -> Half Open

    cb.record_success()
    cb.record_success()  # Needs 2 success threshold

    assert cb.state == CircuitState.CLOSED
    cb.check()  # Should not raise
