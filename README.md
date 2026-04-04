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

## Running the application (SCEMAS)

**Prerequisites:** [Docker Desktop](https://www.docker.com/products/docker-desktop/) running (or another Docker engine with Compose v2).

From the repository root (after `cp .env.example .env` and editing `.env` under `src/`):

```bash
cd src
./start.sh
```

First-time setup (before running the chunk above):

1. Create your env file under `src/` and fill in at least `SUPABASE_DB_URL` and `JWT_SECRET` (see `src/.env.example`):

   ```bash
   cd src
   cp .env.example .env
   ```

2. If `start.sh` is not executable yet: `chmod +x start.sh`

3. Optional flags: `./start.sh --no-build` (faster restart), `./start.sh --regen` (new MQTT certs), `./start.sh --help`

Then open:

- **Frontend:** http://localhost:3000  
- **API docs (Swagger):** http://localhost:8000/docs  

More detail (local dev without Docker, env variables, MQTT notes) is in [`src/README.md`](src/README.md).

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
