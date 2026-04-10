"""
T-Shirt Distribution System — FastAPI Backend
Serves both the API and the frontend (static HTML/CSS/JS).
Uses Google Sheets as the database.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from models import PersonStatus, StatsResponse, ActionResponse, SizeBreakdown
from sheets_db import SheetsDB
import logging
import os

logger = logging.getLogger("main")

# Global database instance
db: SheetsDB = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize Google Sheets connection on startup."""
    global db
    logger.info("🚀 Starting T-Shirt Distribution System...")
    db = SheetsDB()
    stats = db.get_stats()
    logger.info(f"📊 Loaded {stats['total']} participants ({stats['taken']} taken, {stats['remaining']} remaining)")
    yield
    logger.info("👋 Shutting down...")


app = FastAPI(
    title="T-Shirt Distribution System",
    description="QR-based T-Shirt pickup tracker backed by Google Sheets",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow all for scanner access from any device on the network
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ────────────────────── API ROUTES ──────────────────────

@app.get("/api/status/{token_id}", response_model=PersonStatus)
async def get_status(token_id: str):
    """Look up a person by their token ID and return their details + taken status."""
    person = db.find_by_token(token_id)
    if person is None:
        raise HTTPException(status_code=404, detail="Person not found. Invalid QR code.")
    return person


@app.post("/api/mark/{token_id}", response_model=ActionResponse)
async def mark_as_taken(token_id: str):
    """Mark a person's T-shirt as collected."""
    person = db.find_by_token(token_id)
    if person is None:
        raise HTTPException(status_code=404, detail="Person not found.")

    if person["is_taken"]:
        return ActionResponse(
            success=False,
            message=f"T-shirt for {person['name']} was already collected!",
            person=PersonStatus(**person),
        )

    success = db.mark_as_taken(token_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update Google Sheet.")

    # Re-fetch to confirm
    updated = db.find_by_token(token_id)
    return ActionResponse(
        success=True,
        message=f"✅ T-shirt marked as collected for {updated['name']}!",
        person=PersonStatus(**updated),
    )


@app.post("/api/reset/{token_id}", response_model=ActionResponse)
async def reset_status(token_id: str):
    """Reset a person's T-shirt status to not-collected (undo)."""
    person = db.find_by_token(token_id)
    if person is None:
        raise HTTPException(status_code=404, detail="Person not found.")

    success = db.reset(token_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update Google Sheet.")

    updated = db.find_by_token(token_id)
    return ActionResponse(
        success=True,
        message=f"🔄 Reset status for {updated['name']}.",
        person=PersonStatus(**updated),
    )


@app.get("/api/stats", response_model=StatsResponse)
async def get_stats():
    """Get summary statistics (total, taken, remaining, by size)."""
    stats = db.get_stats()
    # Convert raw dicts to SizeBreakdown models
    by_size = {k: SizeBreakdown(**v) for k, v in stats["by_size"].items()}
    return StatsResponse(
        total=stats["total"],
        taken=stats["taken"],
        remaining=stats["remaining"],
        by_size=by_size,
    )


@app.get("/api/participants")
async def get_participants():
    """Get all participants with their status."""
    records = db.get_all_records()
    return {"participants": records, "total": len(records)}


# ────────────────────── FRONTEND ROUTES ──────────────────────

# Mount static files (CSS, JS)
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", response_class=HTMLResponse)
async def home():
    """Serve the scanner home page."""
    return FileResponse(os.path.join(static_dir, "index.html"))


@app.get("/verify/{token_id}", response_class=HTMLResponse)
async def verify_page(token_id: str):
    """Serve the verify page for a specific token."""
    return FileResponse(os.path.join(static_dir, "verify.html"))


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page():
    """Serve the dashboard page."""
    return FileResponse(os.path.join(static_dir, "dashboard.html"))
