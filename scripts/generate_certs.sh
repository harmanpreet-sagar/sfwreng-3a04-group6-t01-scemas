#!/bin/bash
# MQTT TLS Certificate Generation Script
# Generates self-signed certificates for Mosquitto broker (development use only)

set -e  # Exit on any error

echo "=========================================="
echo "Generating MQTT TLS Certificates"
echo "=========================================="

# Navigate to certificate directory
CERT_DIR="$(dirname "$0")/../src/mosquitto/config/certs"
mkdir -p "$CERT_DIR"
cd "$CERT_DIR" || exit 1

# Certificate details
COUNTRY="CA"
STATE="Ontario"
CITY="Hamilton"
ORG="McMaster"
OU="SFWRENG3A04"
DAYS=365

echo "✓ Generating Certificate Authority (CA)..."
# Generate CA private key and self-signed certificate
openssl req -new -x509 -days $DAYS -extensions v3_ca \
    -keyout ca.key -out ca.crt \
    -subj "/C=$COUNTRY/ST=$STATE/L=$CITY/O=$ORG/OU=$OU/CN=MosquittoCA" \
    -nodes

echo "✓ Generating server private key..."
# Generate server private key (2048-bit RSA)
openssl genrsa -out server.key 2048

echo "✓ Creating Certificate Signing Request (CSR)..."
# Generate CSR for server certificate
openssl req -new -key server.key -out server.csr \
    -subj "/C=$COUNTRY/ST=$STATE/L=$CITY/O=$ORG/OU=$OU/CN=mosquitto"

echo "✓ Signing server certificate with CA..."
# Sign server certificate with CA (valid for 365 days)
openssl x509 -req -in server.csr \
    -CA ca.crt -CAkey ca.key -CAcreateserial \
    -out server.crt -days $DAYS

# Set appropriate permissions for private keys
chmod 600 *.key

echo ""
echo "=========================================="
echo "Certificate Generation Complete!"
echo "=========================================="
echo ""
echo "Generated files:"
echo "  - ca.crt        (Certificate Authority)"
echo "  - ca.key        (CA private key)"
echo "  - server.crt    (Server certificate)"
echo "  - server.key    (Server private key)"
echo ""
echo "⚠️  These are self-signed certificates for DEVELOPMENT only"
echo "   Use proper CA-signed certificates in production"
echo ""
