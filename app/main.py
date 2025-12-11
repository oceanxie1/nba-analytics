"""FastAPI application entry point."""
from fastapi import FastAPI
from app.db import init_db
from app.routers import players, teams, games

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
    # Both docs and redoc are available:
    # - /docs = Swagger UI (interactive, try-it-out)
    # - /redoc = ReDoc (cleaner, more readable, often fixes visibility issues)
)

# Include routers
app.include_router(players.router)
app.include_router(teams.router)
app.include_router(games.router)


@app.on_event("startup")
def startup_event():
    """Initialize database on startup."""
    init_db()


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

