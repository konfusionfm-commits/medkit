from __future__ import annotations

import logging
import threading
import time
from enum import Enum
from typing import Optional

from medkit.exceptions import CircuitOpenError

logger = logging.getLogger("medkit.circuit_breaker")


class CircuitState(Enum):
    CLOSED = "CLOSED"  # Normal operation, requests pass through
    OPEN = "OPEN"  # Failing, requests are rejected immediately
    HALF_OPEN = "HALF_OPEN"  # Testing recovery, a single request is allowed


class CircuitBreaker:
    """
    A circuit breaker to prevent cascading failures when a provider is down.
    Maintains internal state and transitions based on success/failure thresholds.
    Thread-safe implementation for use across multiple requests.
    """

    def __init__(
        self,
        provider_name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        success_threshold: int = 2,
    ):
        self.provider_name = provider_name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None

        self._lock = threading.RLock()

    def _transition_to(self, new_state: CircuitState) -> None:
        """Transitions to a new state and resets counters."""
        logger.info(
            f"Circuit breaker for {self.provider_name} transitioned from "
            f"{self.state.value} to {new_state.value}"
        )
        self.state = new_state
        if new_state == CircuitState.CLOSED:
            self.failure_count = 0
            self.success_count = 0
        elif new_state == CircuitState.OPEN:
            self.last_failure_time = time.time()
        elif new_state == CircuitState.HALF_OPEN:
            self.success_count = 0

    def check(self) -> None:
        """
        Check if a request is allowed to proceed.
        Raises CircuitOpenError if the circuit is OPEN and recovery timeout hasn't passed.
        Transitions OPEN -> HALF_OPEN if the timeout has passed.
        """
        with self._lock:
            if self.state == CircuitState.CLOSED:
                return

            if self.state == CircuitState.OPEN:
                # Check if we should allow a test request
                if time.time() - (self.last_failure_time or 0) >= self.recovery_timeout:
                    self._transition_to(CircuitState.HALF_OPEN)
                    return
                raise CircuitOpenError(
                    f"Circuit breaker is OPEN for {self.provider_name}. "
                    f"Failing fast to prevent cascading failure."
                )

            if self.state == CircuitState.HALF_OPEN:
                # We only allow a limited number of test requests.
                # For a strict half-open, we might just allow 1, but we let the caller proceed
                # and record_success/record_failure will handle the rest.
                return

    def record_success(self) -> None:
        """Record a successful request."""
        with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.success_threshold:
                    self._transition_to(CircuitState.CLOSED)
            elif self.state == CircuitState.CLOSED:
                self.failure_count = 0  # Reset on any success

    def record_failure(self) -> None:
        """Record a failed request."""
        with self._lock:
            if self.state == CircuitState.CLOSED:
                self.failure_count += 1
                if self.failure_count >= self.failure_threshold:
                    self._transition_to(CircuitState.OPEN)
            elif self.state == CircuitState.HALF_OPEN:
                # If we fail while half-open, immediately reopen the circuit
                self._transition_to(CircuitState.OPEN)
