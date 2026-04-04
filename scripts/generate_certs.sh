#!/usr/bin/env bash
# Generate self-signed TLS certificates for the Mosquitto MQTT broker.
#
# Run from the repository root:
#   ./scripts/generate_certs.sh
#
# What gets written to src/mosquitto/config/certs/:
#   ca.crt      — CA certificate           DO NOT COMMIT (gitignored)
#   server.crt  — server certificate       DO NOT COMMIT (gitignored)
#   ca.key      — CA private key           DO NOT COMMIT (gitignored)
#   server.key  — server private key       DO NOT COMMIT (gitignored)
#
# All four files are gitignored. Every developer runs this script once after
# cloning. Committing .crt while .key is gitignored causes a key/cert mismatch
# whenever a teammate regenerates the key — all four files must stay in sync locally.
#
# After running, restart Mosquitto to pick up the new certs:
#   docker-compose restart mosquitto
#
# Note: the server CN is "mosquitto".  paho-mqtt clients must call
#   client.tls_insecure_set(True)
# when connecting from localhost because the CN won't match the hostname.
# Use a proper CA cert in production.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CERT_DIR="$REPO_ROOT/src/mosquitto/config/certs"

echo "Writing certificates to: $CERT_DIR"
cd "$CERT_DIR"

# ── Certificate Authority ──────────────────────────────────────────────────────
# -nodes skips the pass-phrase so the Docker daemon can read ca.key without
# interactive input.
openssl req -new -x509 -days 365 -extensions v3_ca \
    -keyout ca.key \
    -out    ca.crt \
    -subj   "/C=CA/ST=Ontario/L=Hamilton/O=McMaster/OU=SFWRENG3A04/CN=MosquittoCA" \
    -nodes

echo "  ca.crt  (commit)"
echo "  ca.key  (DO NOT commit)"

# ── Server certificate ─────────────────────────────────────────────────────────
openssl genrsa -out server.key 2048

openssl req -new \
    -key  server.key \
    -out  server.csr \
    -subj "/C=CA/ST=Ontario/L=Hamilton/O=McMaster/OU=SFWRENG3A04/CN=mosquitto"

openssl x509 -req \
    -in     server.csr \
    -CA     ca.crt \
    -CAkey  ca.key \
    -CAcreateserial \
    -out    server.crt \
    -days   365

rm -f server.csr ca.srl

echo "  server.crt  (commit)"
echo "  server.key  (DO NOT commit)"
echo ""
echo "Done.  Run: docker-compose restart mosquitto"
