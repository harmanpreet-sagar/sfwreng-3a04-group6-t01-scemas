# MQTT TLS Certificates

## Security Notice

**Private keys are NOT committed to version control for security reasons.**

Only public certificates (`.crt` files) are tracked in git. Private keys (`.key` files) must be generated locally by each developer.

## Generating Certificates

Run the setup script to generate all required certificates:

```bash
# From project root
./scripts/setup_dev.sh
```

Or generate certificates manually:

```bash
# From project root
./scripts/generate_certs.sh
```

This will create:
- `ca.key` - Certificate Authority private key (NOT in git)
- `ca.crt` - Certificate Authority certificate (in git)
- `server.key` - Server private key (NOT in git)
- `server.crt` - Server certificate (in git)

## Files in This Directory

- **`ca.crt`** - Public CA certificate (committed)
- **`server.crt`** - Public server certificate (committed)
- **`ca.key`** - Private CA key (generated locally, gitignored)
- **`server.key`** - Private server key (generated locally, gitignored)
- **`server.csr`** - Certificate signing request (temporary, gitignored)

## Production Certificates

For production deployment, replace self-signed certificates with certificates from a trusted Certificate Authority (e.g., Let's Encrypt).
