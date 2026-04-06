# MQTT TLS Certificates

## Security Notice

**All certificate and key files are gitignored and must be generated locally.**

Neither private keys nor public certificates are committed to version control.
Committing `.crt` files while `.key` files are gitignored causes a key/cert mismatch
whenever a teammate regenerates the key — all four files must stay in sync locally.

## First-time setup (run once after cloning)

```bash
# From the repository root
./scripts/generate_certs.sh
```

This generates all four files locally:

| File | Purpose | Committed? |
|---|---|---|
| `ca.key` | CA private key | No — gitignored |
| `ca.crt` | CA certificate | No — gitignored |
| `server.key` | Server private key | No — gitignored |
| `server.crt` | Server certificate signed by CA | No — gitignored |

After generating, restart Mosquitto to pick up the new certs:

```bash
cd src && docker compose restart mosquitto
```

## Production Certificates

For production deployment, replace self-signed certificates with certificates from a trusted Certificate Authority (e.g., Let's Encrypt).
