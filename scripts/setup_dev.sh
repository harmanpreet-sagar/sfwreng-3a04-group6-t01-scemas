#!/bin/bash
# Development Environment Setup Script
# Prepares the project for local development by creating necessary files and configurations

set -e  # Exit on any error

echo "=========================================="
echo "Threshold Management System - Dev Setup"
echo "=========================================="

# Navigate to src directory
cd "$(dirname "$0")/../src" || exit 1

# Check if .env exists, if not create from template
if [ ! -f .env ]; then
    echo "✓ Creating .env from .env.example..."
    cp .env.example .env
    echo "  ⚠️  Please edit .env and fill in your credentials"
else
    echo "✓ .env already exists"
fi

# Check if MQTT certificates exist
if [ ! -f mosquitto/config/certs/server.crt ]; then
    echo "✓ Generating MQTT TLS certificates..."
    cd mosquitto/config/certs
    
    # Generate CA certificate
    openssl req -new -x509 -days 365 -extensions v3_ca \
        -keyout ca.key -out ca.crt \
        -subj "/C=CA/ST=Ontario/L=Hamilton/O=McMaster/OU=SFWRENG3A04/CN=MosquittoCA" \
        -nodes
    
    # Generate server key and certificate
    openssl genrsa -out server.key 2048
    openssl req -new -key server.key -out server.csr \
        -subj "/C=CA/ST=Ontario/L=Hamilton/O=McMaster/OU=SFWRENG3A04/CN=mosquitto"
    openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key \
        -CAcreateserial -out server.crt -days 365
    
    cd ../../..
    echo "  ✓ Certificates generated successfully"
else
    echo "✓ MQTT certificates already exist"
fi

# Create Mosquitto password file if it doesn't exist
if [ ! -f mosquitto/config/passwd ]; then
    echo "✓ Creating default MQTT password file..."
    echo "  ⚠️  Default user: admin / password: admin123"
    echo "  Run 'mosquitto_passwd' to change credentials"
    touch mosquitto/config/passwd
fi

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Edit .env and add your credentials"
echo "  2. Run: docker-compose up --build"
echo "  3. Access frontend at http://localhost:3000"
echo "  4. Access API docs at http://localhost:8000/docs"
echo ""
