# TradeMind Indicator Worker

Docker-only technical indicator calculation microservice for the TradeMind quant platform.

## Features

- **Indicators**: SMA, EMA, RSI, MACD
- **API**: REST endpoints for health, metrics, and calculation
- **Observability**: Prometheus metrics at `/metrics`
- **Deployment**: Docker / Docker Compose only (Python 3.8)

## Quick Start

```bash
docker compose up --build -d
```

Service listens on `http://localhost:8000`.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/metrics` | Prometheus metrics |
| GET | `/indicators` | List supported indicators |
| POST | `/calculate` | Calculate indicator |

### Calculate Example

```bash
curl -X POST http://localhost:8000/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "indicator": "RSI",
    "data": {
      "symbol": "EURUSD",
      "timeframe": "M15",
      "close": [44.34, 44.09, 44.15, 43.61, 44.33, 44.83, 45.10, 45.42, 45.84, 46.08, 45.89, 46.03, 45.61, 46.28, 46.28]
    },
    "params": {"period": 14}
  }'
```

## Configuration

Environment variables (prefix `TRADEMIND_`):

| Variable | Default | Description |
|----------|---------|-------------|
| `TRADEMIND_WORKER_ID` | `xavier-worker-01` | Worker identifier |
| `TRADEMIND_LOG_LEVEL` | `INFO` | Log level |
| `TRADEMIND_PORT` | `8000` | Service port |

Config file: `config/default.yaml`

## Development

Run tests inside Docker:

```bash
docker compose run --rm indicator-worker pytest -q
```

## Architecture

```
indicator-worker/
├── app/
│   ├── api/routes.py       # HTTP routes
│   ├── config/settings.py  # Configuration
│   ├── core/indicators.py  # Indicator math
│   ├── core/metrics.py     # Prometheus
│   ├── model/schemas.py    # Pydantic models
│   ├── service/            # Business logic
│   └── main.py             # FastAPI entry
├── config/default.yaml
├── tests/
├── Dockerfile
└── docker-compose.yml
```
