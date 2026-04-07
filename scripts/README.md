# Scripts — Developer Utility Scripts

Utility scripts for development setup, certificate management, database migrations, and diagram compilation.

## Scripts

### `setup_dev.sh`

First-time development environment setup. Installs dependencies and prepares the workspace.

```bash
./scripts/setup_dev.sh
```

### `generate_certs.sh`

Generates self-signed TLS certificates for the Mosquitto MQTT broker. Called automatically by `src/start.sh` when certificates are missing, but can be run manually to force-regenerate them.

```bash
./scripts/generate_certs.sh
```

Certificates are written to `src/mosquitto/config/certs/` (gitignored).

### `apply_backend_migrations.sh`

Applies all SQL migration files in `src/backend/db/migrations/` to the database in numeric order. Run this against a fresh database before starting the backend for the first time.

```bash
./scripts/apply_backend_migrations.sh
```

Requires `SUPABASE_DB_URL` to be set in `src/.env`.

### `compile_diagrams.sh`

Batch-compiles all PlantUML source files under `docs/diagrams/plantuml/` to PNG images, writing output to `docs/diagrams/compiled/`.

```bash
./scripts/compile_diagrams.sh
```

Requires `plantuml` to be installed and on `PATH`.

## Usage

Make scripts executable before running:

```bash
chmod +x scripts/*.sh
```
