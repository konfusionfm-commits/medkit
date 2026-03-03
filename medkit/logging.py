from __future__ import annotations

import logging
import sys
from typing import Any

# Conditional import for structlog so the SDK doesn't hard-crash if not installed
# although it will be added to dependencies.
try:
    import structlog

    HAS_STRUCTLOG = True
except ImportError:
    HAS_STRUCTLOG = False


def setup_logging(level: str = "WARNING", json_format: bool = False) -> None:
    """
    Configures structured logging for the MedKit SDK.
    If structlog is installed, uses it for JSON or colored console output.
    Otherwise, falls back to standard python logging.
    """
    numeric_level = getattr(logging, level.upper(), logging.WARNING)
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=numeric_level,
    )

    if not HAS_STRUCTLOG:
        return

    # Structlog configuration
    processors: list[Any] = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if json_format:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> Any:
    """
    Returns a structured logger if structlog is available,
    otherwise returns a standard standard Python logger.
    """
    if HAS_STRUCTLOG:
        return structlog.get_logger(name)
    return logging.getLogger(name)
