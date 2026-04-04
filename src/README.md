# Source Code

## Project Setup

### Prerequisites

- Docker Desktop
- Docker Compose
- Node.js 20+ (for local development)
- Python 3.11+ (for local development)

### Quick Start

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd SFWRENG-3A04-Group6-T01/src
   ```

2. **Configure environment variables**

   ```bash
   cp .env.example .env
   # Edit .env and fill in all required values
   ```

3. **Start all services** (recommended — generates MQTT certs if missing, then builds and runs the stack)

   ```bash
   chmod +x start.sh   # once, if needed
   ./start.sh
   ```

   Or start Compose directly:

   ```bash
   docker compose up --build
   ```

   Subsequent restarts when dependencies have not changed: `./start.sh --no-build`

4. **Access the application**
   - Frontend: <http://localhost:3000>
   - Backend API: <http://localhost:8000>
   - API Documentation: <http://localhost:8000/docs>
   - MQTT Broker: localhost:8883 (TLS enabled)

### Project Structure

```bash
/backend               # FastAPI backend service
  /app
    /routers          # API route handlers
    /models           # Database models
    /services         # Business logic services
    /shared           # Shared utilities and helpers
  main.py             # Application entry point
  requirements.txt    # Python dependencies
  Dockerfile          # Backend container configuration

/frontend             # React + TypeScript frontend
  /src
    /pages            # Page components
    /components       # Reusable UI components
    /types            # TypeScript type definitions
    /api              # API client functions
  package.json        # Node.js dependencies
  Dockerfile          # Frontend container configuration

/mosquitto            # MQTT Broker configuration
  /config
    mosquitto.conf    # Broker configuration with TLS
    /certs            # TLS certificates
      ca.crt          # Certificate Authority
      server.crt      # Server certificate
      server.key      # Server private key

docker-compose.yml    # Multi-service orchestration
.env                  # Environment variables (not committed)
.env.example          # Environment variables template
```

### Development

#### Backend Development

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

#### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

### MQTT TLS Configuration

The project includes self-signed TLS certificates for secure MQTT communication. These are suitable for development but should be replaced with proper certificates in production.

To regenerate certificates:

```bash
cd mosquitto/config/certs
openssl req -new -x509 -days 365 -extensions v3_ca -keyout ca.key -out ca.crt -subj "/C=CA/ST=Ontario/L=Hamilton/O=McMaster/OU=SFWRENG3A04/CN=MosquittoCA" -nodes
openssl genrsa -out server.key 2048
openssl req -new -key server.key -out server.csr -subj "/C=CA/ST=Ontario/L=Hamilton/O=McMaster/OU=SFWRENG3A04/CN=mosquitto"
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out server.crt -days 365
```

### Environment Variables

Copy `.env.example` to `.env` and configure:

- **SUPABASE_URL**: Your Supabase project URL
- **SUPABASE_DB_URL**: Direct database connection string
- **DEMO_PUBLIC_API_KEY** (optional): Plaintext demo key seeded into `api_keys` at startup (hashed in DB). If unset, a fixed dev default from `backend/app/shared/api_key_seed.py` is used. Apply `backend/db/migrations/002_create_api_keys.sql` before expecting the seed to succeed.
- **JWT_SECRET**: Secret key for JWT token signing
- **TWILIO_ACCOUNT_SID**: Twilio account identifier
- **TWILIO_AUTH_TOKEN**: Twilio authentication token
- **TWILIO_FROM_NUMBER**: Phone number for sending SMS
- **TWILIO_TO_NUMBER**: Default recipient phone number
- **MQTT_BROKER_HOST**: MQTT broker hostname (default: mosquitto)
- **MQTT_BROKER_PORT**: MQTT broker port (default: 8883)

### Docker Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Rebuild services
docker-compose up --build

# Stop and remove volumes
docker-compose down -v
```

### API Documentation

Once the backend is running, visit <http://localhost:8000/docs> for interactive API documentation (Swagger UI).

## Team

**Harmanpreet** - Threshold Management + DevOps + API Facade

Group 6 - Tutorial 01
