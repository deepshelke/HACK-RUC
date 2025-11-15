#!/usr/bin/env python3
"""
Run the FastAPI server.
"""
import uvicorn
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    port = int(os.getenv("API_PORT", 8000))
    host = os.getenv("API_HOST", "0.0.0.0")
    
    print("="*70)
    print("Starting Fairly Chat API Server")
    print("="*70)
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"CORS Origins: {os.getenv('CORS_ORIGINS', 'http://localhost:3000')}")
    print("="*70)
    print("\nAPI Documentation available at: http://localhost:8000/docs")
    print("="*70)
    
    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        reload=True  # Auto-reload on code changes
    )

