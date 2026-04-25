# TDX API Local Maintenance

This directory contains the TDX API service source code migrated into the
`aiagents-stock` repository for centralized maintenance.

## Local Development

Run the service from the web module:

```bash
cd tdx-api/web
GOCACHE=/tmp/aiagents-stock-tdx-gocache go run .
```

The service listens on:

```text
http://127.0.0.1:8080
```

Useful checks:

```bash
curl http://127.0.0.1:8080/api/health
curl "http://127.0.0.1:8080/api/quote?code=000001"
```

## Docker Compose

The root `docker-compose.yml` builds this service as `tdx-api` and exposes it on
host port `8080`.

The backend container should use:

```text
TDX_ENABLED=true
TDX_BASE_URL=http://tdx-api:8080
```

Local non-container development should use:

```text
TDX_ENABLED=true
TDX_BASE_URL=http://127.0.0.1:8080
```

## Runtime Data

TDX runtime databases are generated under `data/database` by default. They are
not committed to source control and are persisted through the `tdx-data` Docker
volume in the root Compose setup.
