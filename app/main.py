"""FastAPI application entry point."""

from fastapi import FastAPI, Request, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging
import traceback

from app.db import init_db
from app.routers import players, teams, games
from app.cache import cache_manager, cache_stats

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="NBA Analytics API",
    description="Backend API for NBA analytics platform",
    version="0.1.0",
    # Configure Swagger UI to fix white text on white background issue
    swagger_ui_parameters={
        "syntaxHighlight.theme": "obsidian",  # Dark theme for better visibility
        "tryItOutEnabled": True,
        "persistAuthorization": True,
    },
)


# Global exception handler (catches all exceptions except HTTPException)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions and return JSON response."""
    # Don't handle HTTPException here - let FastAPI handle it
    if isinstance(exc, HTTPException):
        raise exc
    
    error_trace = traceback.format_exc()
    logger.error(f"Unhandled exception: {str(exc)}\n{error_trace}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": f"Internal server error: {str(exc)}"}
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors and return JSON response."""
    logger.error(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()}
    )


# CORS for frontend framework (e.g., React/Vite on localhost:5173)
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(players.router)
app.include_router(teams.router)
app.include_router(games.router)


@app.on_event("startup")
def startup_event():
    """Initialize database and log cache status on startup."""
    init_db()
    if cache_manager.enabled:
        logger.info("✅ Redis cache is ENABLED and connected")
    else:
        logger.warning("⚠️  Redis cache is DISABLED - caching will not work")
        logger.warning("   Make sure Redis is installed: pip install redis")
        logger.warning("   And Redis server is running: redis-cli ping")


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": "NBA Analytics API",
        "docs": "/docs",
        "version": "0.1.0"
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/cache/stats")
def get_cache_stats():
    """Get cache performance statistics.
    
    Returns:
    - Cache hit/miss counts
    - Hit rate percentage
    - Average response times (with/without cache)
    - Speedup factor
    - Time saved per request
    """
    stats = cache_stats.get_stats()
    return {
        "cache_enabled": cache_manager.enabled,
        "statistics": stats
    }


@app.post("/cache/stats/reset")
def reset_cache_stats():
    """Reset cache statistics."""
    cache_stats.reset()
    return {"message": "Cache statistics reset"}

