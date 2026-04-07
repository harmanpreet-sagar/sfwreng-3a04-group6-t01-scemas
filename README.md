# SCEMAS — Smart Campus Environmental Monitoring and Alert System

**Course:** SFWRENG 3A04 - Software Design III | McMaster University | Winter 2026  
**Group:** Group 6 - Tutorial 01

## What We Built

SCEMAS is a full-stack environmental monitoring platform that ingests real-time sensor telemetry over MQTT, evaluates configurable alert thresholds, and streams live alerts to a web dashboard. The system supports JWT-authenticated user accounts, Twilio SMS notifications for critical alerts, aggregated historical data with charted rollups, a data validation pipeline, and a public-facing API with rate-limited API key access and an interactive zone map.

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, Leaflet, Recharts |
| Backend | FastAPI (Python 3.11), asyncio background workers |
| Messaging | Eclipse Mosquitto MQTT broker (TLS on port 8883) |
| Database | PostgreSQL via Supabase |
| Auth | JWT (python-jose) + bcrypt passwords |
| Notifications | Twilio SMS (optional) |
| Container | Docker Compose |

### Team

| Member | Subsystems |
|--------|-----------|
| Aakash Satishkumar | Alerts Management, API Management |
| Ali Shareeff | Data Validation |
| Harmanpreet Singh Sagar | Threshold Management, API Facade, DevOps |
| Jason Kim | Account Management, Public API |
| Praneet Singh | Aggregation Management |

---

## Project Structure

```bash
SFWRENG-3A04-Group6-T01/
├── docs/                               # Design artifacts and UML diagrams
│   └── diagrams/
│       ├── drawio/                     # Draw.io analysis class diagram
│       └── plantuml/
│           ├── class/                  # Class diagrams (one per subsystem + combined)
│           ├── sequence/               # Sequence diagrams (BE1-BE8)
│           ├── state/                  # State charts (one per subsystem)
│           └── usecase/                # Use case diagrams
├── vercel.json                         # Vercel: build src/frontend from repo root
├── scripts/                            # Developer utility scripts
│   ├── apply_backend_migrations.sh     # Run all DB migration files in order
│   ├── compile_diagrams.sh             # Batch-compile all PlantUML files to PNG
│   ├── generate_certs.sh               # Generate Mosquitto TLS certificates
│   └── setup_dev.sh                    # First-time dev environment setup
│
├── src/                                # All application source code
│   ├── docker-compose.yml              # Orchestrates frontend, backend, mosquitto
│   ├── start.sh                        # Helper: generates certs + runs Compose
│   ├── .env.example                    # Environment variable template
│   ├── Simulator.py                    # Publishes fake sensor readings over MQTT
│   │
│   ├── backend/                        # FastAPI backend service
│   │   ├── main.py                     # App entry point; registers all routers & workers
│   │   ├── requirements.txt            # Python dependencies
│   │   ├── Dockerfile
│   │   ├── pytest.ini
│   │   ├── app/
│   │   │   ├── routers/                # HTTP route handlers (one file per subsystem)
│   │   │   │   ├── accounts.py         # User account CRUD + admin operations
│   │   │   │   ├── aggregation.py      # Aggregated telemetry queries
│   │   │   │   ├── alerts.py           # Alert listing, acknowledgement, SSE stream
│   │   │   │   ├── public_demo.py      # Unauthenticated demo endpoints
│   │   │   │   ├── public_zones.py     # Public zone status (API-key protected)
│   │   │   │   ├── thresholds.py       # Threshold CRUD
│   │   │   │   └── validation.py       # Data validation event endpoints
│   │   │   ├── services/               # Business logic layer
│   │   │   │   ├── accounts_service.py
│   │   │   │   ├── aggregated_data_repository.py
│   │   │   │   ├── aggregation_service.py
│   │   │   │   ├── alert_repository.py
│   │   │   │   ├── alert_service.py
│   │   │   │   ├── api_key_repository.py
│   │   │   │   ├── notification_service.py  # Twilio SMS dispatch
│   │   │   │   ├── public_zones_service.py
│   │   │   │   ├── threshold_evaluation.py
│   │   │   │   ├── threshold_repository.py
│   │   │   │   ├── threshold_service.py
│   │   │   │   ├── validation_events_repository.py
│   │   │   │   └── validation_service.py
│   │   │   ├── models/                 # Pydantic response/request models
│   │   │   │   ├── public_api_key.py
│   │   │   │   └── public_zone.py
│   │   │   ├── shared/                 # Cross-cutting utilities
│   │   │   │   ├── auth.py             # JWT creation & verification
│   │   │   │   ├── db.py               # Async DB connection pool
│   │   │   │   ├── enums.py            # Shared enumerations (severity, metric types)
│   │   │   │   ├── alert_sse_broadcaster.py  # SSE push for live alerts
│   │   │   │   ├── public_api_rate_limiter.py
│   │   │   │   ├── public_api_audit_middleware.py
│   │   │   │   └── seed_accounts.py    # Default account seeding at startup
│   │   │   └── tasks/                  # Async background workers
│   │   │       ├── mqtt_subscriber.py       # MQTT → DB ingestion
│   │   │       ├── aggregation_worker.py    # Periodic 5-min/hourly rollups
│   │   │       └── threshold_evaluator_worker.py  # Polls readings, fires alerts
│   │   ├── db/
│   │   │   ├── migrations/             # Ordered SQL migration files (001–024)
│   │   │   └── seeds/                  # Demo seed data
│   │   ├── tests/                      # pytest test suite
│   │   │   ├── conftest.py
│   │   │   ├── test_aggregation.py
│   │   │   ├── test_alerts.py
│   │   │   ├── test_public_api.py
│   │   │   └── test_thresholds.py
│   │   └── scripts/                    # One-off operational scripts
│   │       ├── backfill_hourly_max_from_five_minute_max.py
│   │       ├── demo_alert_pipeline.py
│   │       └── test_twilio_sms.py
│   │
│   ├── frontend/                       # React + Vite frontend
│   │   ├── Dockerfile
│   │   ├── package.json
│   │   ├── index.html
│   │   └── src/
│   │       ├── App.tsx                 # Root component with routing
│   │       ├── main.tsx                # React entry point
│   │       ├── api/                    # Axios API client functions
│   │       │   ├── client.ts           # Configured axios instance
│   │       │   ├── accounts.ts
│   │       │   ├── aggregation.ts
│   │       │   ├── alerts.ts
│   │       │   ├── auth.ts
│   │       │   ├── publicZones.ts
│   │       │   ├── thresholds.ts
│   │       │   └── validation.ts
│   │       ├── components/             # Reusable UI components
│   │       │   ├── AlertPanel.tsx
│   │       │   ├── AlertsBrowserModal.tsx
│   │       │   ├── AggregationHistoryChart.tsx
│   │       │   ├── MetricGauge.tsx
│   │       │   ├── ThresholdTable.tsx
│   │       │   ├── ThresholdFormModal.tsx
│   │       │   ├── ZoneMap.tsx
│   │       │   ├── PublicLandingMap.tsx
│   │       │   ├── SeverityBadge.tsx
│   │       │   ├── SeverityChart.tsx
│   │       │   ├── ViolationAlertModal.tsx
│   │       │   └── ...
│   │       ├── pages/                  # Route-level page components
│   │       │   ├── LandingPage.tsx     # Public zone map (unauthenticated)
│   │       │   ├── LoginPage.tsx
│   │       │   ├── RegisterRequestPage.tsx
│   │       │   ├── AccountPage.tsx     # User profile & account management
│   │       │   └── ThresholdsPage.tsx  # Threshold CRUD + alert dashboard
│   │       ├── context/
│   │       │   └── AuthContext.tsx     # Global auth state (JWT)
│   │       ├── lib/                    # Utility helpers
│   │       │   ├── aqi.ts              # Air quality index calculations
│   │       │   ├── metrics.ts          # Metric formatting
│   │       │   └── sseAlerts.ts        # SSE client for live alerts
│   │       └── types/
│   │           └── index.ts            # Shared TypeScript interfaces
│   │
│   └── mosquitto/                      # MQTT broker
│       └── config/
│           ├── mosquitto.conf          # Broker config (TLS, auth, ports)
│           ├── passwd                  # MQTT username/password file
│           └── certs/                  # TLS certificates (gitignored, generated locally)
│
└── tests/                              # Top-level test documentation
```

---

## How to Run

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (includes Compose v2)
- Git and Bash (Git Bash on Windows)

### 1. Clone and configure

```bash
git clone <repository-url>
cd SFWRENG-3A04-Group6-T01/src
cp .env.example .env
```

Open `src/.env` and set at minimum:

```env
SUPABASE_DB_URL=postgresql://postgres:[password]@[host]:5432/postgres
JWT_SECRET=<any-strong-random-string>
```

For SMS alerts, also fill in the `TWILIO_*` variables and set `TWILIO_SMS_ENABLED=true`.

### 2. Start the stack

```bash
cd src
chmod +x start.sh   # once, on Linux/Mac (not needed on Windows Git Bash)
./start.sh
```

`start.sh` generates Mosquitto TLS certificates if they are missing, then calls `docker compose up --build`.

| Flag | Effect |
|------|--------|
| *(none)* | Build images if needed and start all services |
| `--no-build` | Faster restart when only mounted source files changed |
| `--regen` | Regenerate MQTT TLS certificates |
| `--help` | Show usage |

### 3. Open the app

| Service | URL |
|---------|-----|
| Web UI | <http://localhost:3000> |
| Backend API + Swagger | <http://localhost:8000/docs> |
| MQTT broker (TLS) | localhost:8883 |

### 4. Apply database migrations

If this is the first time connecting to a fresh database, run the migrations:

```bash
cd ..    # repository root
chmod +x scripts/apply_backend_migrations.sh
./scripts/apply_backend_migrations.sh
```

### 5. Stop the stack

```bash
cd src
docker compose down
```

---

## Running Without Docker (Local Dev)

### Backend

```bash
cd src/backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd src/frontend
npm install
npm run dev     # Vite dev server at http://localhost:5173
```

Set `VITE_API_URL=http://localhost:8000` in `src/frontend/.env.local` if the dev server cannot reach the backend.

---

## Running Tests

Backend tests use **pytest** and live in `src/backend/tests/`:

```bash
cd src/backend
source venv/bin/activate
pytest
```

---

## Deployment (Vercel + Render)

The frontend is a static Vite build; the backend is a long-running FastAPI process with background workers. They are usually deployed separately.

### Frontend — Vercel (Git)

1. In the Vercel dashboard, **Import** your existing GitHub repository (do not use the flow that creates a *new* empty Git repo).
2. **Root Directory:** leave empty (repository root). The repo includes `vercel.json`, which installs and builds `src/frontend` and publishes `src/frontend/dist`.
3. **Project name:** lowercase only (e.g. `sfwreng-3a04-group6-t01`); Vercel rejects uppercase in the project slug.
4. **Production branch:** set to `main` (or your release branch) under Project → Settings → Git.
5. **Environment variables** (Settings → Environment Variables), then **redeploy** so Vite picks them up at build time:

| Variable | Required | Description |
|----------|----------|-------------|
| `VITE_API_URL` | Yes (production) | Public URL of the backend, e.g. `https://your-api.onrender.com` — **no trailing slash** |
| `VITE_PUBLIC_DEMO_API_KEY` | No | Must match backend `DEMO_PUBLIC_API_KEY` if the public zone map should call `/public/zones` from the browser |

Client-side routing uses SPA fallback rules in `vercel.json`; deep links should load the app correctly.

### Backend — Render (Docker)

1. Create a **Web Service**, connect the **same** Git repository.
2. **Root Directory:** leave empty so the build uses the **repository root** `Dockerfile`, which copies `src/backend/` into the image. (Alternatively: Root Directory `src/backend` and Dockerfile `Dockerfile` inside that folder.)
3. **Runtime:** Docker.
4. Set **environment variables** (at minimum):

| Variable | Description |
|----------|-------------|
| `JWT_SECRET` | Strong random secret for JWT signing |
| `SUPABASE_DB_URL` | PostgreSQL connection string (Supabase) |
| `CORS_ALLOW_ORIGINS` | Comma-separated frontend origins, **no trailing slashes**, e.g. `https://your-app.vercel.app` or `https://your-app.vercel.app,http://localhost:3000`. If unset, the API defaults to `allow_origins=["*"]` (OK for local dev only). |
| `MQTT_*` | On Render there is no local `mosquitto` service. Point `MQTT_BROKER_HOST` / port / user / password at a **public** broker (e.g. HiveMQ Cloud). For TLS with a public CA, set `MQTT_CA_CERT_PATH=SYSTEM`. See `src/.env.example`. |
| `DEMO_PUBLIC_API_KEY`, Twilio vars | Optional; same semantics as local `.env` |

5. Redeploy after changing env vars.

### Connect frontend and backend

1. Deploy the backend first; copy its HTTPS origin.
2. Set **`VITE_API_URL`** on Vercel to that origin (no trailing slash) and redeploy the frontend.
3. Set **`CORS_ALLOW_ORIGINS`** on Render to your Vercel origin (exact scheme + host, no path, no trailing slash).

### Repository layout for deploys

| Path | Role |
|------|------|
| `vercel.json` | Vercel: install/build frontend from repo root |

---

## Design Diagrams

PlantUML source files are under `docs/diagrams/plantuml/`. To compile them to PNG:

```bash
# Single diagram
plantuml docs/diagrams/plantuml/class/SCEMAS.puml

# All diagrams
./scripts/compile_diagrams.sh
```

Rendered images are written to `docs/diagrams/compiled/` (gitignored).
