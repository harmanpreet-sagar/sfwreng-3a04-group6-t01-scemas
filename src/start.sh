#!/usr/bin/env bash
# ============================================================
# SCEMAS dev startup script
# Works on Linux, macOS, and Windows (Git Bash / WSL)
#
# Usage (run from the src/ directory):
#   ./start.sh            # normal start — rebuilds images
#   ./start.sh --no-build # fast restart — skips image rebuild
#   ./start.sh --regen    # force-regenerate TLS certs + rebuild
#   ./start.sh --help     # show this message
# ============================================================

# Exit immediately on any error, treat unset variables as errors,
# and propagate pipe failures. This prevents silent half-starts.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CERT_DIR="$SCRIPT_DIR/mosquitto/config/certs"
NO_BUILD=false
REGEN_CERTS=false

# ── Parse flags ───────────────────────────────────────────────
for arg in "$@"; do
  case "$arg" in
    --no-build)  NO_BUILD=true ;;
    --regen)     REGEN_CERTS=true ;;
    --help|-h)
      echo "Usage: ./start.sh [--no-build] [--regen]"
      echo "  (no flags)  Build Docker images and start all services"
      echo "  --no-build  Skip image rebuild (faster restart after code changes)"
      echo "  --regen     Force-regenerate MQTT TLS certificates (needed after cert expiry or corruption)"
      exit 0 ;;
  esac
done

# All paths are relative to SCRIPT_DIR (the src/ directory) so the script
# works correctly regardless of where it is invoked from.
cd "$SCRIPT_DIR"

# ── Check Docker is available ─────────────────────────────────
if ! command -v docker &>/dev/null; then
  echo "❌ Docker not found. Install Docker Desktop and try again."
  exit 1
fi

# Detect whether the Docker Compose v2 plugin (`docker compose`) or the
# legacy v1 standalone binary (`docker-compose`) is installed.
# Both are supported so the script works on older Docker Desktop versions
# as well as the current CLI.
if docker compose version &>/dev/null 2>&1; then
  DC="docker compose"
elif command -v docker-compose &>/dev/null; then
  DC="docker-compose"
else
  echo "❌ Neither 'docker compose' nor 'docker-compose' found."
  exit 1
fi

# ── Step 1: TLS certificates ──────────────────────────────────
# Mosquitto requires TLS certificates to be present before it starts.
# We generate them using openssl run inside an alpine Docker container
# instead of the host's openssl for two reasons:
#   1. Portability: not all systems have openssl installed (especially Windows).
#   2. Path mangling: Git Bash on Windows converts POSIX paths in openssl -subj
#      arguments (e.g. /C=CA) to Windows paths (e.g. C:/CA), producing
#      malformed certificates. Running inside a Linux container avoids this.
# MSYS_NO_PATHCONV=1 suppresses Git Bash path conversion for the docker run
# command itself (specifically the -v volume flag). It is a no-op on Linux/macOS.
CERTS_PRESENT=false
if [[ -f "$CERT_DIR/ca.crt" && -f "$CERT_DIR/server.crt" ]]; then
  CERTS_PRESENT=true
fi

if [[ "$REGEN_CERTS" == true || "$CERTS_PRESENT" == false ]]; then
  echo ""
  echo "🔐 Generating MQTT TLS certificates via Docker..."
  mkdir -p "$CERT_DIR"

  MSYS_NO_PATHCONV=1 docker run --rm \
    -v "$CERT_DIR:/certs" \
    alpine sh -c "
      apk add --no-cache openssl -q 2>/dev/null

      # Step 1a: Generate a self-signed CA certificate (365-day validity).
      # The -nodes flag omits the private key passphrase so Mosquitto can
      # load the key without interactive input at startup.
      openssl req -new -x509 -days 365 \
        -keyout /certs/ca.key -out /certs/ca.crt \
        -subj '/C=CA/ST=Ontario/CN=MosquittoCA' -nodes

      # Step 1b: Generate the broker's private key and a certificate signing request.
      openssl genrsa -out /certs/server.key 2048
      openssl req -new -key /certs/server.key -out /tmp/server.csr \
        -subj '/C=CA/ST=Ontario/CN=mosquitto'

      # Step 1c: Sign the broker's CSR with the CA. CAcreateserial generates
      # a serial number file automatically (ca.srl), which we remove afterwards.
      openssl x509 -req \
        -in /tmp/server.csr \
        -CA /certs/ca.crt -CAkey /certs/ca.key -CAcreateserial \
        -out /certs/server.crt -days 365

      # Clean up temporary files — only the CA cert, CA key, server cert,
      # and server key need to be retained for Mosquitto.
      rm -f /tmp/server.csr /certs/ca.srl
    "
  echo "✅ Certificates ready"
else
  echo "✅ TLS certificates already present — use --regen to force-regenerate"
fi

# ── Step 2: Tear down stale containers + anonymous volumes ─────
# `down -v` removes all anonymous volumes declared in docker-compose.yml.
# This is critical for the frontend: without it, a stale node_modules volume
# from a previous image build can shadow the freshly installed packages inside
# the new image (e.g. hiding tailwindcss after it was first added), causing
# Vite to fail with "Cannot find module 'tailwindcss'" at startup.
# `|| true` prevents the script from exiting if no containers are running.
echo ""
echo "🧹 Removing stale containers and volumes..."
$DC down -v 2>/dev/null || true

# ── Step 3: Start the stack ────────────────────────────────────
# --build forces Docker to rebuild images even if the layer cache is warm.
# This is the safe default since Python/Node dependencies change frequently.
# Use --no-build to skip the rebuild when only source files have changed
# and the installed dependencies are up to date.
echo ""
if [[ "$NO_BUILD" == true ]]; then
  echo "🚀 Starting containers (skipping rebuild)..."
  $DC up
else
  echo "🚀 Building images and starting all services..."
  $DC up --build
fi
