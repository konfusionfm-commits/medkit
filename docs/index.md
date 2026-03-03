# MedKit Documentation

Welcome to MedKit! This documentation outlines the v3.0.0 features.

## Quickstart

Initialize the `AsyncMedKit` client. Automatically leverages the `RetryEngine`, fallback endpoints, and `structlog`.

```python
from medkit import AsyncMedKit

async with AsyncMedKit() as medkit:
    print(await medkit.health_check_async())
```
