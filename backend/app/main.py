"""
GREENWAVE FastAPI Application Entrypoint.
"""
import os
import sys
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse

# Ensure project root is in sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.app.config.settings import settings
from backend.app.models.database import init_db
from backend.app.api.routes import router as api_router
from backend.app.api.websocket import router as ws_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Real-Time Intelligent Traffic Signal Control Using YOLO and Reinforcement Learning",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for frontend dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Database on app startup
@app.on_event("startup")
def on_startup():
    init_db()

# Mount API Routers
app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(api_router)  # Also allow top-level /health, /metrics for direct calls
app.include_router(ws_router)

# Mount Dashboard Static Files if they exist
static_dir = root_dir / "dashboard" / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Serve main dashboard HTML
@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    index_file = root_dir / "dashboard" / "templates" / "index.html"
    if index_file.exists():
        return HTMLResponse(content=index_file.read_text())
    return HTMLResponse(content="<h1>GREENWAVE API is running</h1><p>Visit <a href='/docs'>/docs</a> for API specifications.</p>")

# Serve standalone interactive demo
@app.get("/demo", response_class=HTMLResponse)
async def serve_demo():
    demo_file = root_dir / "docs-site" / "index.html"
    if demo_file.exists():
        return HTMLResponse(content=demo_file.read_text())
    return HTMLResponse(content="<h1>Demo page not found</h1>")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
