# Scripts

Utility scripts for development, deployment, and maintenance tasks.

## Purpose

Automate common tasks like certificate generation, database migrations, diagram compilation, and deployment procedures.

## Planned Scripts

### Development Scripts

**`setup_dev.sh`** - Initial development environment setup
```bash
#!/bin/bash
# Install dependencies, generate certificates, create .env from template
```

**`compile_diagrams.sh`** - Batch compile all PlantUML diagrams
```bash
#!/bin/bash
# Convert all .puml files to PNG images in docs/diagrams/compiled/
```

### Certificate Management

**`generate_certs.sh`** - Regenerate MQTT TLS certificates
```bash
#!/bin/bash
# Generate new self-signed certificates for Mosquitto broker
```

### Database Scripts

**`migrate_db.py`** - Run database migrations
```python
# Apply schema changes to Supabase database
```

**`seed_db.py`** - Populate database with test data
```python
# Insert sample thresholds, users, and telemetry for testing
```

### Deployment Scripts

**`deploy.sh`** - Production deployment automation
```bash
#!/bin/bash
# Build Docker images, push to registry, deploy to server
```

## Usage

Make scripts executable before running:
```bash
chmod +x scripts/*.sh
./scripts/setup_dev.sh
```
