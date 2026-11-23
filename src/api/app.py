"""FastAPI application setup."""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from ..database import init_db
from .routes import emails, classifications, drafts, audit, triage


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    Path("./data").mkdir(exist_ok=True)
    await init_db()
    yield


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="AI Inbox Triage Agent",
        description="Intelligent email classification and response drafting with human approval workflow",
        version="1.0.0",
        lifespan=lifespan,
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.include_router(emails.router, prefix="/api/emails", tags=["Emails"])
    app.include_router(classifications.router, prefix="/api/classifications", tags=["Classifications"])
    app.include_router(drafts.router, prefix="/api/drafts", tags=["Drafts"])
    app.include_router(audit.router, prefix="/api/audit", tags=["Audit"])
    app.include_router(triage.router, prefix="/api/triage", tags=["Triage"])
    
    @app.get("/api/health")
    async def health_check():
        return {"status": "healthy", "service": "ai-inbox-triage"}

    # Serve built frontend if present (Docker / production)
    static_dir = Path(__file__).resolve().parents[2] / "static"
    if static_dir.exists():
        app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
    
    return app


app = create_app()
