"""Main FastAPI application."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.database import init_db
from app.routers import company, clients, zus, expenses, taxes, web


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan events."""
    # Startup
    await init_db()
    yield
    # Shutdown
    pass


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Polish Accounting Application API for IT freelancers and small businesses",
    lifespan=lifespan
)

# Setup templates for simple HTML interface (temporary for testing)
templates = Jinja2Templates(directory="templates")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(company.router)
app.include_router(clients.router)
app.include_router(zus.router)
app.include_router(expenses.router)
app.include_router(taxes.router)
app.include_router(web.router)


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint for health check."""
    return {
        "message": f"Welcome to {settings.app_name} API",
        "version": settings.app_version,
        "status": "healthy"
    }


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "service": settings.app_name}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
