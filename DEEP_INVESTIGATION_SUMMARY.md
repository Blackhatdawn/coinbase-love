# Deep Investigation Summary

This document provides a guide to using the `/api/deep-investigation` endpoint and interpreting its output.

## Endpoint

`GET /api/deep-investigation`

## Description

This endpoint provides a comprehensive diagnostic report of the backend system's health. It checks the status of the system, environment configuration, database, Redis, and other critical services.

## Sample Response

```json
{
  "report_generated_at": "2023-10-27T10:00:00.000Z",
  "investigation_duration_ms": 150.75,
  "summary": {
    "all_systems_go": true,
    "status": "HEALTHY"
  },
  "details": {
    "system": {
      "cpu_percent": 12.5,
      "memory_percent": 58.3,
      "disk_percent": 45.2
    },
    "configuration": {
      "environment": "production",
      "sentry_enabled": true,
      "cors_origins_configured": true,
      "rate_limiting_enabled": true
    },
    "database": {
      "status": "connected"
    },
    "redis": {
      "status": "connected"
    },
    "external_services": {
      "coincap": {
        "status": "healthy"
      }
    }
  }
}
```

## Interpreting the Output

- `report_generated_at`: The timestamp when the report was generated.
- `investigation_duration_ms`: The time it took to generate the report, in milliseconds.
- `summary`:
    - `all_systems_go`: A boolean indicating if all checks passed.
    - `status`: `HEALTHY` if all checks passed, `DEGRADED` otherwise.
- `details`:
    - `system`: Basic system metrics.
    - `configuration`: Key application configuration settings.
    - `database`: The status of the database connection.
    - `redis`: The status of the Redis connection.
    - `external_services`: The status of external services like CoinCap.
