# SFWRENG 3A04 - Group 6 - Tutorial 01

Software Design III Project Repository

## Course Information

**Course:** SFWRENG 3A04 - Software Design III  
**Term:** Winter 2026  
**Institution:** McMaster University

## Team

Group 6 - Tutorial 01

### Members

- Aakash Satishkumar
- Ali Shareeff
- Harmanpreet Singh Sagar
- Jason Kim
- Praneet Singh

## Project Structure

```bash
├── docs/                     # All documentation and design artifacts
│   ├── diagrams/             # UML diagrams and design models
│   │   ├── plantuml/         # PlantUML source files (.puml)
│   │   │   ├── usecase/      # Use case diagrams
│   │   │   ├── class/        # Class diagrams
│   │   │   ├── sequence/     # Sequence diagrams
│   │   │   └── state/        # State diagrams
│   │   ├── drawio/           # Draw.io source files
│   │   └── compiled/         # Generated diagram images (PNG/SVG)
│   ├── reports/              # Project deliverables and reports
│   └── images/               # Screenshots, mockups, and other images
│       ├── screenshots/
│       └── mockups/
├── src/                      # Application source (FastAPI, React, Docker Compose, start.sh)
```

## How to run the app (SCEMAS)

The stack is **MQTT (Mosquitto)**, **FastAPI backend**, and **React (Vite) frontend**, orchestrated with **Docker Compose**. Use the helper script from `src/` so TLS certs and Compose are set up correctly.

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (or Docker Engine + **Compose v2**: `docker compose`, not the legacy `docker-compose` binary)
- Git

### 1. Environment file

All runtime secrets and URLs are read from **`src/.env`** (Compose loads it from that directory).

```bash
cd src
cp .env.example .env
```

Edit `src/.env` and set at least:

- **`SUPABASE_DB_URL`** — PostgreSQL connection string (Supabase)
- **`JWT_SECRET`** — any strong random string (required for login / protected routes)

Fill in Twilio and other keys as needed for your setup; see comments in `src/.env.example` and [`src/README.md`](src/README.md#environment-variables).

### 2. Start the stack

```bash
cd src
chmod +x start.sh    # only once, if your shell says “permission denied”
./start.sh
```

This generates Mosquitto TLS certs if they are missing, builds images when needed, and starts **frontend**, **backend**, and **broker**.

| Script flag | Purpose |
|-------------|---------|
| *(none)* | Build images (if needed) and start services |
| `./start.sh --no-build` | Faster restart when you only changed mounted code |
| `./start.sh --regen` | Regenerate MQTT TLS certificates |
| `./start.sh --help` | Show usage |

### 3. Open the app

| Service | URL |
|---------|-----|
| **Web UI** | [http://localhost:3000](http://localhost:3000) |
| **API (Swagger)** | [http://localhost:8000/docs](http://localhost:8000/docs) |
| **MQTT (TLS)** | `localhost:8883` (used by backend/simulator inside Docker) |

### 4. Stop the stack

From `src/`:

```bash
docker compose down
```

(Use `docker-compose down` only if your machine still has the old v1 CLI.)

### Running without Docker (optional)

For **backend** or **frontend** only on your machine, use Node 20+ and Python 3.11+ as described in [`src/README.md`](src/README.md) under **Development**. You still need PostgreSQL (and usually MQTT) reachable at the URLs in your env files.

### Frontend builds (`npm`)

Node dependencies and scripts live under **`src/frontend/`**, not `src/`. For a production build:

```bash
cd src/frontend
npm install
npm run build
```

## Getting Started (documentation & diagrams)

### Prerequisites

- PlantUML (for diagram generation)
- Draw.io (for editing .drawio files)

### Compiling PlantUML Diagrams

To generate PNG images from PlantUML files:

```bash
# Compile a single diagram
plantuml docs/diagrams/plantuml/usecase/usecase_diagram_2_revised.puml -o ../compiled

# Compile all diagrams
plantuml docs/diagrams/plantuml/**/*.puml -o ../compiled
```
