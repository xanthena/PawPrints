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

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

from app.pet_profiles import (
    DEFAULT_PROFILE_DIR,
    MAX_PETS,
    list_pet_profiles,
    register_pet_profile,
    remove_pet_profile,
)
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
        "image_url": f"/media/pet-profiles/{profile.image_path.name}",
        "created_at": profile.created_at,
    }


@app.get("/api/pets")
async def get_pets():
    return {
        "pets": [_pet_profile_dict(profile) for profile in list_pet_profiles()],
        "max_pets": MAX_PETS,
    }


@app.post("/api/pets")
async def create_pet(name: str = Form(...), image: UploadFile = File(...)):
    """Registers one named reference photo (JPEG/PNG) for pet identification.

    The image is staged to a temp file first because PetProfileStore
    validates and copies from a real path on disk -- it doesn't know
    about UploadFile's async, request-scoped stream.
    """
    suffix = _pet_image_suffix(image.filename)
    staging_path = UPLOADS_DIR / f".pet-upload-{pipeline_runner.new_job_id()}{suffix}"
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(staging_path, "wb") as out:
            out.write(await image.read())
        profile = register_pet_profile(name, staging_path)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
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


def _pet_image_suffix(filename):
    suffix = Path(filename or "").suffix.lower()
    return suffix if suffix in {".jpg", ".jpeg", ".png"} else ".jpg"


@app.get("/api/models")
async def get_models():
    return {"models": sorted(SUPPORTED_MODELS)}


@app.post("/api/footage/analyze")
async def analyze_footage(
    request: Request,
    file: UploadFile = File(...),
    primary_model: str | None = None,
    fallback_model: str | None = None,
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


@app.get("/api/health")
async def health():
    return {"status": "ok"}
