"""
FastAPI Server Entry Point for SEO Automation Platform.
"""

import logging
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.routes.monitoring import router as monitoring_router
from api.routes.pages import router as pages_router
from api.routes.pipeline import router as pipeline_router
from api.routes.projects import router as projects_router

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

app = FastAPI(
    title="SEO Automation Platform API",
    description="Full-stack API for autonomous niche keyword research, site architecture, first-wave content generation, and v0.4 GSC Indexing Watch.",
    version="0.4.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS for local and production frontend dashboards
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers with /api/v1 prefix
app.include_router(projects_router, prefix="/api/v1")
app.include_router(pipeline_router, prefix="/api/v1")
app.include_router(pages_router, prefix="/api/v1")
app.include_router(monitoring_router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "version": "0.4.0", "service": "seo-automation-api"}


@app.get("/", tags=["Root"])
def root():
    """Root entry point directing to interactive OpenAPI docs."""
    return {
        "service": "SEO Automation Platform API",
        "version": "0.4.0",
        "documentation": "/docs",
        "endpoints": {
            "projects": "/api/v1/projects",
            "pipeline": "/api/v1/pipeline",
            "pages": "/api/v1/projects/{project_id}/pages",
            "monitoring": "/api/v1/monitoring/{project_id}/dashboard",
        },
    }
