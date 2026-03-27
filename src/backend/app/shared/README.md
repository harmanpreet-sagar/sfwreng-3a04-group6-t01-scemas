# Shared

Shared utilities, helpers, and common functionality used across the application.

## Purpose

Reusable components that don't fit into routers, models, or services. This includes utilities for authentication, database connections, configuration management, and common helpers.

## Structure

```python
# Example: auth.py
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer
import jwt

security = HTTPBearer()

def verify_token(token: str) -> dict:
    # Verify JWT token and extract claims
    pass

# Example: database.py
from supabase import create_client
import os

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)
```

## Planned Shared Components

- `auth.py` - JWT authentication utilities
- `database.py` - Database connection and client
- `dependencies.py` - FastAPI dependency injection functions
- `config.py` - Application configuration management
- `exceptions.py` - Custom exception classes
