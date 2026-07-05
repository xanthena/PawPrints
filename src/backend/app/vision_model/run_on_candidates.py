import json
import sys
from pathlib import Path

from paths import DATA_DIR, FRAMES_DIR, JSONS_DIR, REPO_ROOT
import model_router

EVENTS_DIR = DATA_DIR / "events"


def load_candidates(video_stem):
    """Read events.jsonl for video_stem and keep only vision-bound candidates
    -- burst_end markers have no frame and cost nothing, so they're skipped
    here rather than sent to the model."""
    events_path = EVENTS_DIR / video_stem / "events.jsonl"

    with events_path.open("r", encoding="utf-8") as f:
        events = [json.loads(line) for line in f if line.strip()]

    return [event for event in events if event["kind"] == "candidate"]


def run(video_stem, preferred_model=None):
    """preferred_model overrides VISION_MODEL_PREFERENCE for this run --
    this is the hook a future API/UI toggle would call through."""
    candidates = load_candidates(video_stem)
    results = []

    for candidate in candidates:
        frame_path = candidate["frame_path"]
        print(f"Analyzing candidate: {Path(frame_path).name} (trigger={candidate['trigger']})")

        outcome = model_router.analyze(frame_path, allowed_dir=str(FRAMES_DIR), preferred=preferred_model)
        raw_output = outcome["output"]

        if isinstance(raw_output, str):
            try:
                result = json.loads(raw_output)
            except Exception:
                result = {"raw_output": raw_output}
        else:
            result = raw_output

        results.append({
            "frame": Path(frame_path).name,
            "timestamp": candidate["timestamp"],
            "frame_number": candidate["frame_index"],
            "result": result,
            "model_used": outcome["model_used"],
            "fell_back": outcome["fell_back"],
        })

    JSONS_DIR.mkdir(parents=True, exist_ok=True)
    output_file = JSONS_DIR / f"{video_stem}_vision.json"
    with output_file.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)

    print(f"Saved {len(results)} results to {output_file.relative_to(REPO_ROOT)}")
    return results


if __name__ == "__main__":
    video_stem = sys.argv[1] if len(sys.argv) > 1 else "cat_inbag"
    preferred_model = sys.argv[2] if len(sys.argv) > 2 else None
    run(video_stem, preferred_model=preferred_model)
