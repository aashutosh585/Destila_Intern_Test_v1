from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .routers import exceptions, dashboard
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")
except Exception as e:
    logger.error(f"Error creating database tables: {e}")

app = FastAPI(
    title="Production Exception Monitoring API",
    description="API for monitoring production deficit exceptions",
    version="1.0.0"
)

# CORS middleware for frontend
frontend_origins = [
    origin.strip()
    for origin in os.getenv("FRONTEND_ORIGINS", "https://destila-intern-test-v1-pqh1.vercel.app,http://localhost:5173,http://localhost:3000").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=frontend_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers (both at root and with /api prefix for Vercel routing compatibility)
app.include_router(exceptions.router)
app.include_router(dashboard.router)
app.include_router(exceptions.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")


@app.get("/")
def root():
    return {
        "message": "Production Exception Monitoring API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}
