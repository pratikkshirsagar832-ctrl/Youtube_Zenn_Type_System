"""Nexus FastAPI server — minimal endpoints for v1.

v1 endpoints (no YouTube OAuth, no auto-publish):
  GET  /api/health        - liveness check + service status
  POST /api/generate      - start a new video project (topic/url/script)
  GET  /api/status/{id}   - live status of a project
  GET  /api/projects      - list all projects
  GET  /api/download/{id} - download the final MP4
"""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from config import (
    BACKEND_HOST,
    BACKEND_PORT,
    FRONTEND_URL,
    PROJECTS_DIR,
    is_fully_configured,
    DEFAULT_DURATION_MINUTES,
    DEFAULT_NICHE,
    VALID_NICHES,
)
from pipeline import run_pipeline, PipelineInput

# --- App ---
app = FastAPI(
    title="Nexus — Autonomous YouTube Video Factory",
    version="1.0.0",
    description="Minimal FastAPI server for the Nexus pipeline.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Request / Response models ---
class GenerateRequest(BaseModel):
    input: str = Field(..., description="Topic text, YouTube URL, or full script (auto-detected)")
    duration_minutes: int = Field(DEFAULT_DURATION_MINUTES, ge=5, le=8, description="5, 6, 7, or 8 minutes")
    niche: str = Field(DEFAULT_NICHE, description="One of: " + ", ".join(VALID_NICHES))
    force_mode: str | None = Field(None, description="'topic' | 'reference' | 'script' (auto-detect if None)")


class GenerateResponse(BaseModel):
    project_id: str
    mode: str
    duration_minutes: int
    niche: str
    status: str = "queued"
    created_at: str


class ProjectSummary(BaseModel):
    project_id: str
    topic: str
    niche: str
    duration_minutes: int
    status: str
    current_stage: str
    progress: float
    created_at: str
    mp4_path: str | None = None


# --- Helpers ---
def _detect_mode(text: str) -> str:
    """Auto-detect whether the input is a topic, YouTube URL, or full script."""
    t = text.strip()
    if "youtube.com/watch?v=" in t or "youtu.be/" in t:
        return "reference"
    if len(t.split()) > 100:
        return "script"
    return "topic"


def _save_project_metadata(project_id: str, metadata: dict) -> None:
    path = PROJECTS_DIR / project_id / "status.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(metadata, indent=2, default=str), encoding="utf-8")


def _load_project_metadata(project_id: str) -> dict | None:
    path = PROJECTS_DIR / project_id / "status.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _list_projects() -> list[dict]:
    out = []
    for p in sorted(PROJECTS_DIR.iterdir(), reverse=True):
        if not p.is_dir():
            continue
        meta = _load_project_metadata(p.name)
        if meta:
            out.append(meta)
    return out


# --- Background runner ---
async def _run_pipeline_background(project_id: str, inp: PipelineInput) -> None:
    """Run the pipeline and persist progress into status.json as it goes."""
    def on_progress(stage: str, message: str, progress: float) -> None:
        meta = _load_project_metadata(project_id) or {}
        meta.update({
            "project_id": project_id,
            "current_stage": stage,
            "progress": progress,
            "last_message": message,
            "updated_at": datetime.utcnow().isoformat() + "Z",
        })
        _save_project_metadata(project_id, meta)

    try:
        result = await run_pipeline(inp, on_progress=on_progress)
        meta = _load_project_metadata(project_id) or {}
        meta.update({
            "project_id": project_id,
            "status": "ready",
            "current_stage": "complete",
            "progress": 1.0,
            "mp4_path": str(result.get("mp4_path", "")),
            "total_duration_seconds": result.get("total_duration_seconds", 0.0),
            "completed_at": datetime.utcnow().isoformat() + "Z",
        })
        _save_project_metadata(project_id, meta)
    except Exception as exc:
        meta = _load_project_metadata(project_id) or {}
        meta.update({
            "project_id": project_id,
            "status": "failed",
            "error": str(exc),
            "failed_at": datetime.utcnow().isoformat() + "Z",
        })
        _save_project_metadata(project_id, meta)


# --- Serve frontend ---
FRONTEND_DIR = Path(__file__).resolve().parent / "frontend"
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="frontend")


@app.get("/", response_class=HTMLResponse)
async def index():
    return HTMLResponse((FRONTEND_DIR / "index.html").read_text(encoding="utf-8"))


# --- Endpoints ---
@app.get("/api/health")
async def health() -> dict:
    return {
        "status": "ok",
        "version": app.version,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "services": is_fully_configured(),
    }


@app.post("/api/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest, background: BackgroundTasks) -> GenerateResponse:
    if req.niche not in VALID_NICHES:
        raise HTTPException(400, f"Invalid niche. Use one of: {VALID_NICHES}")

    mode = req.force_mode or _detect_mode(req.input)
    project_id = uuid.uuid4().hex[:12]
    created_at = datetime.utcnow().isoformat() + "Z"

    metadata = {
        "project_id": project_id,
        "topic": req.input[:200] if mode == "topic" else (req.input if mode == "script" else req.input),
        "mode": mode,
        "niche": req.niche,
        "duration_minutes": req.duration_minutes,
        "status": "queued",
        "current_stage": "queued",
        "progress": 0.0,
        "created_at": created_at,
        "updated_at": created_at,
    }
    _save_project_metadata(project_id, metadata)

    inp = PipelineInput(
        project_id=project_id,
        user_input=req.input,
        mode=mode,
        niche=req.niche,
        duration_minutes=req.duration_minutes,
    )
    background.add_task(_run_pipeline_background, project_id, inp)

    return GenerateResponse(
        project_id=project_id,
        mode=mode,
        duration_minutes=req.duration_minutes,
        niche=req.niche,
        status="queued",
        created_at=created_at,
    )


@app.get("/api/status/{project_id}")
async def status(project_id: str) -> dict:
    meta = _load_project_metadata(project_id)
    if not meta:
        raise HTTPException(404, f"Project {project_id} not found")
    return meta


@app.get("/api/projects")
async def projects() -> dict:
    return {"projects": _list_projects()}


@app.get("/api/download/{project_id}")
async def download(project_id: str):
    meta = _load_project_metadata(project_id)
    if not meta:
        raise HTTPException(404, f"Project {project_id} not found")
    mp4 = meta.get("mp4_path")
    if not mp4 or not Path(mp4).exists():
        raise HTTPException(404, "MP4 not ready. Check /api/status/{id}")
    topic = meta.get("topic", "nexus_video")[:40]
    safe_name = "".join(c if c.isalnum() or c in " -_" else "_" for c in topic).strip() or "nexus_video"
    filename = f"{safe_name}.mp4"
    return FileResponse(
        mp4,
        media_type="video/mp4",
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=BACKEND_HOST, port=BACKEND_PORT, reload=True)
