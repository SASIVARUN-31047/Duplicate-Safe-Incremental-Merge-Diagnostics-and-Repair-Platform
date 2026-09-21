from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone

app = FastAPI(
    title="Duplicate-Safe Incremental Merge Diagnostics & Repair Platform",
    description="Backend API for detecting, attributing, repairing, and auditing data duplicate records.",
    version="1.0.0"
)

# Enable CORS for local development and Vercel deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {
        "project": "Duplicate-Safe Incremental Merge Diagnostics & Repair Platform (DEAI-10)",
        "status": "online",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "backend-api",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
