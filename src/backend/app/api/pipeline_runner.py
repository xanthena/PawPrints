"""
Runs the full backend pipeline for one uploaded video as a single
generator, yielding one JSON-serializable dict per line (NDJSON) as
each stage produces something new:

    motion detection -> candidate frame -> vision model -> event
    timeline -> (at the end) highlight reel

This treats the video the same way a live camera feed eventually will
be treated: frames arrive one at a time, motion detection runs on each
one as it arrives, and every candidate frame is sent to the vision
model and folded into the event timeline immediately -- there is no
"process everything, then show results" step. The only thing that is
actually specific to "a finished file" rather than "a live feed" is
that this generator terminates and triggers a highlight reel once the
video runs out; a live source would just keep going.

The frontend consumes this as a streamed HTTP response (see
app.api.server) and updates its UI after every yielded event instead
of waiting for the whole thing to finish.
"""

import sys
import uuid
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[2]
VISION_MODEL_DIR = BACKEND_ROOT / "app" / "vision_model"

# vision_model's own modules (model_router.py, main_run_on_candidates.py)
# use bare imports like `from models import local_qwen` and `import
# model_router`, which only resolve if the vision_model directory itself
# is on sys.path -- this mirrors how a developer running those scripts
# directly from that directory would work.
if str(VISION_MODEL_DIR) not in sys.path:
    sys.path.insert(0, str(VISION_MODEL_DIR))

import cv2 as cv  # noqa: E402

from app.event_builder.event_pipeline import run_event_pipeline  # noqa: E402
from app.highlight_reel.pipeline import generate_highlight_reel  # noqa: E402
from app.highlight_reel.paths import OUTPUT_DIR as REEL_OUTPUT_DIR  # noqa: E402
from app.motion_detector.main_stream_worker import (  # noqa: E402
    FRAMES_DIR,
    persist_event,
    stream_events,
)

import model_router  # noqa: E402  (see sys.path note above)

REPO_ROOT = BACKEND_ROOT.parents[1]
DATA_DIR = REPO_ROOT / "src" / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
JSONS_DIR = DATA_DIR / "jsons"
EVENTS_DIR = DATA_DIR / "events"

COOLDOWN_SEC = 4.0
STILL_PING_INTERVAL_SEC = 300.0


def new_job_id():
    return uuid.uuid4().hex[:12]


def save_upload(job_id, filename, file_obj):
    """Persist an uploaded video to disk and return its path."""
    job_dir = UPLOADS_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(filename or "footage.mp4").suffix or ".mp4"
    video_path = job_dir / f"source{suffix}"
    with open(video_path, "wb") as out:
        while True:
            chunk = file_obj.read(1024 * 1024)
            if not chunk:
                break
            out.write(chunk)
    return video_path


def probe_duration_seconds(video_path):
    vid = cv.VideoCapture(str(video_path))
    if not vid.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")
    fps = vid.get(cv.CAP_PROP_FPS) or 30
    frame_count = vid.get(cv.CAP_PROP_FRAME_COUNT) or 0
    vid.release()
    return frame_count / fps if fps else 0.0


def run_pipeline(job_id, video_path, primary_model=None, fallback_model=None, should_continue=None):
    """
    Yields dicts describing pipeline progress, in this rough shape:

      {"type": "started", "job_id", "duration_seconds", "video_url"}
      {"type": "progress", "processed_seconds", "duration_seconds"}
      {"type": "candidate", "timestamp", "trigger", "frame_url", "activity"}
      {"type": "timeline", "events": [...]}   -- full timeline, replace-in-place
      {"type": "reel_ready", "reel_url", "manifest"}
      {"type": "cancelled"}
      {"type": "done"}
      {"type": "error", "message"}

    Any exception raised mid-pipeline is caught and turned into a final
    {"type": "error"} event rather than propagating, since this runs
    inside a streaming HTTP response where a raised exception can no
    longer become a normal error status code.

    `should_continue`, if given, is polled at each safe checkpoint (between
    sampled frames, and before each vision-model call) -- letting a caller
    whose client has disconnected (closed tab, page reload) ask this to
    stop instead of grinding through the rest of the video for an
    audience that isn't listening anymore. It is never polled mid-call
    (e.g. while a vision-model request is in flight), since that work
    can't be interrupted cooperatively -- the worst case is finishing the
    one call already in progress before noticing.
    """
    if should_continue is None:
        should_continue = lambda: True  # noqa: E731

    video_stem = job_id
    vision_json = JSONS_DIR / f"{video_stem}_vision.json"
    timeline_json = JSONS_DIR / f"{video_stem}_final_timeline.json"

    try:
        duration_seconds = probe_duration_seconds(video_path)
    except Exception as exc:
        yield {"type": "error", "message": f"Could not read video: {exc}"}
        return

    yield {
        "type": "started",
        "job_id": job_id,
        "duration_seconds": duration_seconds,
        "video_url": f"/media/uploads/{job_id}/{Path(video_path).name}",
    }

    vision_results = []
    out_dir = EVENTS_DIR / video_stem

    try:
        for event in stream_events(
            video_path,
            cooldown_sec=COOLDOWN_SEC,
            still_ping_interval_sec=STILL_PING_INTERVAL_SEC,
        ):
            if not should_continue():
                yield {"type": "cancelled"}
                return

            persisted = persist_event(dict(event), out_dir, video_stem)

            yield {
                "type": "progress",
                "processed_seconds": persisted["timestamp"],
                "duration_seconds": duration_seconds,
            }

            if persisted["kind"] != "candidate":
                continue

            # the previous candidate's span just ended -- this timestamp
            # is when it stopped being the most current evidence
            if vision_results:
                vision_results[-1]["end_time"] = persisted["timestamp"]

            if not should_continue():
                yield {"type": "cancelled"}
                return

            outcome = model_router.analyze(
                persisted["frame_path"],
                allowed_dir=str(FRAMES_DIR),
                primary=primary_model,
                fallback=fallback_model,
            )
            result = _parse_vision_output(outcome["output"])

            vision_results.append({
                "frame": Path(persisted["frame_path"]).name,
                "timestamp": persisted["timestamp"],
                "end_time": persisted["timestamp"],
                "frame_number": persisted["frame_index"],
                "result": result,
                "model_used": outcome["model_used"],
                "fell_back": outcome["fell_back"],
            })
            JSONS_DIR.mkdir(parents=True, exist_ok=True)
            _write_json(vision_json, vision_results)

            # run_event_pipeline is what actually knows how to pull a clean
            # "activity" label out of raw model output (stripping markdown
            # fences, defaulting unknowns, etc, via clean_results) -- reuse
            # its output for the live preview instead of re-guessing here.
            final_events = run_event_pipeline(vision_json, timeline_json)
            latest_activity = final_events[-1]["activity"] if final_events else None

            yield {
                "type": "candidate",
                "timestamp": persisted["timestamp"],
                "trigger": persisted["trigger"],
                "frame_url": f"/media/frames/{Path(persisted['frame_path']).name}",
                "activity": latest_activity,
            }
            yield {"type": "timeline", "events": final_events}

        if not vision_results:
            yield {"type": "done", "reel_generated": False}
            return

        if not should_continue():
            yield {"type": "cancelled"}
            return

        # A too-short or too-uneventful video can leave the selector with
        # nothing to include -- that's a normal outcome, not a pipeline
        # failure, so it gets its own event instead of erroring out a job
        # whose timeline already streamed successfully.
        try:
            reel_path, _manifest_path, manifest = generate_highlight_reel(
                timeline_path=timeline_json,
                video_path=video_path,
                output_dir=REEL_OUTPUT_DIR,
            )
        except ValueError as exc:
            yield {"type": "reel_skipped", "reason": str(exc)}
            yield {"type": "done", "reel_generated": False}
            return

        yield {
            "type": "reel_ready",
            "reel_url": f"/media/results/{reel_path.relative_to(REEL_OUTPUT_DIR).as_posix()}",
            "manifest": manifest,
        }
        yield {"type": "done", "reel_generated": True}

    except Exception as exc:  # noqa: BLE001 -- surfaced to the client, not swallowed
        yield {"type": "error", "message": str(exc)}


def _parse_vision_output(raw_output):
    if not isinstance(raw_output, str):
        return raw_output
    import json

    try:
        return json.loads(raw_output)
    except Exception:
        return {"raw_output": raw_output}


def _write_json(path, data):
    import json

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
