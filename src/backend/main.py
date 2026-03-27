"""
Main FastAPI application entry point for the Threshold Management System.
This module initializes the API Facade layer that routes requests to subsystem services.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

# Load environment variables from .env file for local development
# In production, these should be injected via container orchestration
load_dotenv()

# Initialize FastAPI application with OpenAPI documentation metadata
app = FastAPI(
    title="SFWRENG 3A04 - Group 6 API",
    description="Backend API for Threshold Management System",
    version="1.0.0"
)

# Enable CORS to allow frontend (running on different port/domain) to make requests
# TODO: Restrict allow_origins to specific domains in production for security
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint for basic API verification."""
    return {"message": "Welcome to Group 6 API"}

@app.get("/health")
async def health_check():
    """Health check endpoint for container orchestration and monitoring."""
    return {"status": "healthy"}

# Direct execution entry point for local development without Docker
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
