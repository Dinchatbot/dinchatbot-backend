# app/main.py
"""
DinChatbot - Professional AI Chatbot Backend
FastAPI + Gemini + PostgreSQL
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
import logging

from app.core.config import settings
from app.core.database import engine, Base
from app.api import chat, leads, training, branding, handover, admin
from app.core.logging import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="DinChatbot API",
    description="Professional AI-powered customer service chatbot",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production: specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request ID and timing middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = f"req_{int(time.time())}_{id(request)}"
    request.state.request_id = request_id
    request.state.start_time = time.time()
    
    response = await call_next(request)
    
    latency_ms = int((time.time() - request.state.start_time) * 1000)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Latency-MS"] = str(latency_ms)
    
    return response

# Error handling
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(
        f"Unhandled exception",
        extra={
            "request_id": getattr(request.state, "request_id", None),
            "path": request.url.path,
            "error": str(exc),
        },
        exc_info=True,
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "request_id": getattr(request.state, "request_id", None),
        },
    )

# Include routers
app.include_router(chat.router, prefix="/api", tags=["Chat"])
app.include_router(leads.router, prefix="/api", tags=["Leads"])
app.include_router(training.router, prefix="/api", tags=["Training"])
app.include_router(branding.router, prefix="/api", tags=["Branding"])
app.include_router(handover.router, prefix="/api", tags=["Handover"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "version": "2.0.0",
        "features": {
            "ai": True,
            "lead_capture": True,
            "handover": True,
            "branding": True,
            "url_training": True,
        },
    }

# Root endpoint
@app.get("/")
async def root():
    """API information"""
    return {
        "name": "DinChatbot API",
        "version": "2.0.0",
        "docs": "/api/docs",
        "health": "/health",
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info(
        "Server starting",
        extra={
            "version": "2.0.0",
            "environment": settings.ENVIRONMENT,
            "ai_enabled": bool(settings.OPENAI_API_KEY),
        },
    )

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Server shutting down")

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.ENVIRONMENT == "development",
        log_level="info",
    )
