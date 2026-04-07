# Tests

Top-level placeholder for the test directory. All backend tests live in `src/backend/tests/`.

## Backend Tests

Tests are written with **pytest** and live in `src/backend/tests/`:

| File | What it covers |
|------|---------------|
| `conftest.py` | Shared fixtures (test DB client, auth headers, seed data) |
| `test_aggregation.py` | Aggregation service and rollup queries |
| `test_alerts.py` | Alert creation, acknowledgement, and SSE delivery |
| `test_public_api.py` | Public zone endpoints and API key authentication |
| `test_thresholds.py` | Threshold CRUD and evaluation logic |

## Running Tests

```bash
cd src/backend
source venv/bin/activate      # Windows: venv\Scripts\activate
pytest
```

Or with verbose output:

```bash
pytest -v
```

To run a single test file:

```bash
pytest tests/test_alerts.py -v
```
