"""
Minimal FastAPI service exposing the streaming pipeline to the frontend.

Run from src/backend with:

    uvicorn app.api.server:app --reload --port 8000

One endpoint does the whole job: POST a video, get back a streamed
NDJSON response (one JSON object per line) that the frontend reads
incrementally as the pipeline works through the video. There's no
separate "upload" then "poll for status" step -- the HTTP response
itself IS the live progress feed.
"""

import asyncio
import json
import threading
from pathlib import Path

import ollama
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.pet_profiles import (
    DEFAULT_PROFILE_DIR,
    MAX_PETS,
    add_pet_image,
    list_pet_profiles,
    register_pet_profile,
    remove_pet_profile,
)
from app.query_layer import answer_query
from app.vision_model.model_router import _VALID_MODELS as SUPPORTED_MODELS

from . import pipeline_runner
from .pipeline_runner import DATA_DIR, REEL_OUTPUT_DIR, UPLOADS_DIR

app = FastAPI(title="PawPrints pipeline API")

# The Vite dev server runs on a different port, so the browser treats
# this as cross-origin -- allow it explicitly rather than disabling
# CORS checks project-wide.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

FRAMES_DIR = DATA_DIR / "frames"
FRAMES_DIR.mkdir(parents=True, exist_ok=True)
REEL_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/media/frames", StaticFiles(directory=str(FRAMES_DIR)), name="frames")
app.mount("/media/results", StaticFiles(directory=str(REEL_OUTPUT_DIR)), name="results")
# Lets the dashboard play back the source video itself (for the
# processing-detail modal) while it's still being analyzed.
app.mount("/media/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

PET_IMAGES_DIR = DEFAULT_PROFILE_DIR / "images"
PET_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/media/pet-profiles", StaticFiles(directory=str(PET_IMAGES_DIR)), name="pet-profiles")

_SENTINEL = object()


def _pet_profile_dict(profile):
    return {
        "id": profile.profile_id,
        "name": profile.name,
        "image_urls": [f"/media/pet-profiles/{path.name}" for path in profile.image_paths],
        "created_at": profile.created_at,
    }


def _pet_image_suffix(filename):
    suffix = Path(filename or "").suffix.lower()
    return suffix if suffix in {".jpg", ".jpeg", ".png"} else ".jpg"


async def _stage_upload(image: UploadFile):
    """Copy an UploadFile to a real temp path -- PetProfileStore validates
    and copies from an actual path on disk, not an async request stream."""
    suffix = _pet_image_suffix(image.filename)
    staging_path = UPLOADS_DIR / f".pet-upload-{pipeline_runner.new_job_id()}{suffix}"
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    with open(staging_path, "wb") as out:
        out.write(await image.read())
    return staging_path


@app.get("/api/pets")
async def get_pets():
    return {
        "pets": [_pet_profile_dict(profile) for profile in list_pet_profiles()],
        "max_pets": MAX_PETS,
    }


@app.post("/api/pets")
async def create_pet(name: str = Form(...), images: list[UploadFile] = File(...)):
    """Registers a pet with one or more reference photos (JPEG/PNG)."""
    staging_paths = [await _stage_upload(image) for image in images]
    try:
        profile = register_pet_profile(name, staging_paths)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        for path in staging_paths:
            path.unlink(missing_ok=True)

    return _pet_profile_dict(profile)


@app.post("/api/pets/{identifier}/images")
async def add_pet_photo(identifier: str, image: UploadFile = File(...)):
    """Adds another reference photo to an already-registered pet."""
    staging_path = await _stage_upload(image)
    try:
        profile = add_pet_image(identifier, staging_path)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    finally:
        staging_path.unlink(missing_ok=True)

    return _pet_profile_dict(profile)


@app.delete("/api/pets/{identifier}")
async def delete_pet(identifier: str):
    try:
        profile = remove_pet_profile(identifier)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _pet_profile_dict(profile)


@app.get("/api/models")
async def get_models():
    return {"models": sorted(SUPPORTED_MODELS)}


@app.get("/api/ollama-models")
async def get_ollama_models():
    """Locally-pulled Ollama models, for the Settings UI's model picker --
    "qwen" as a provider covers any vision-capable model Ollama is
    actually serving, not just qwen2.5vl:3b, so the choice of *which*
    one needs to come from what's really available on this machine."""
    try:
        response = ollama.list()
    except Exception as exc:
        return {"models": [], "error": f"Could not reach Ollama: {exc}"}
    return {"models": [model.model for model in response.models]}


@app.post("/api/footage/analyze")
async def analyze_footage(
    request: Request,
    file: UploadFile = File(...),
    primary_model: str | None = None,
    fallback_model: str | None = None,
    ollama_model: str | None = None,
):
    """
    Accepts one uploaded video and streams pipeline progress back as
    NDJSON. The video is saved to disk up front (UploadFile is an
    async, request-scoped handle that a synchronous generator run in a
    worker thread can't safely read from later), then the pipeline runs
    synchronously against that saved file in a background thread.

    If the client goes away mid-stream (closed tab, page reload), a
    watcher task notices via `request.is_disconnected()` and asks the
    pipeline to stop at its next safe checkpoint, rather than leaving it
    to grind through the rest of the video -- burning CPU/GPU time and
    piling up frames/JSON for a result nobody will ever see.
    """
    job_id = pipeline_runner.new_job_id()
    video_path = pipeline_runner.save_upload(job_id, file.filename, file.file)

    loop = asyncio.get_event_loop()
    queue = asyncio.Queue()
    cancel_event = threading.Event()

    def worker():
        try:
            for event in pipeline_runner.run_pipeline(
                job_id,
                video_path,
                primary_model=primary_model,
                fallback_model=fallback_model,
                ollama_model=ollama_model,
                should_continue=lambda: not cancel_event.is_set(),
            ):
                loop.call_soon_threadsafe(queue.put_nowait, event)
        finally:
            loop.call_soon_threadsafe(queue.put_nowait, _SENTINEL)

    threading.Thread(target=worker, daemon=True).start()

    async def watch_disconnect():
        try:
            while not cancel_event.is_set():
                if await request.is_disconnected():
                    cancel_event.set()
                    return
                await asyncio.sleep(1.0)
        except asyncio.CancelledError:
            pass

    watcher = asyncio.ensure_future(watch_disconnect())

    async def event_stream():
        try:
            while True:
                item = await queue.get()
                if item is _SENTINEL:
                    break
                yield json.dumps(item, ensure_ascii=False) + "\n"
        finally:
            # Covers both directions: if we get here because the pipeline
            # is done, stop the now-pointless watcher; if we get here
            # because the client disconnected (this generator gets
            # closed early), make sure the pipeline thread finds out too.
            cancel_event.set()
            watcher.cancel()

    return StreamingResponse(event_stream(), media_type="application/x-ndjson")


class QueryRequest(BaseModel):
    question: str
    start_date: str | None = None
    end_date: str | None = None


@app.post("/api/query")
async def query_activities(payload: QueryRequest):
    """Answers a natural-language question over every day's final timeline
    (e.g. "did my cat play in the last 3 days?") using the deterministic,
    evidence-backed query_layer -- no LLM call, no proof video (kept fast
    for a chat-style UI); every match still comes with its supporting
    timeline evidence in the response."""
    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="A question is required.")
    try:
        return answer_query(
            question,
            start_date=payload.start_date,
            end_date=payload.end_date,
            include_proof=False,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/health")
async def health():
    return {"status": "ok"}
