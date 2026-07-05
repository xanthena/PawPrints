import json
import sys
from pathlib import Path

from paths import DATA_DIR, FRAMES_DIR, JSONS_DIR, REPO_ROOT
import model_router

EVENTS_DIR = DATA_DIR / "events"


def load_events(video_stem):
    events_path = EVENTS_DIR / video_stem / "events.jsonl"

    with events_path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def compute_end_time(all_events, index):
    """
    Every candidate ends when the next event of any kind begins --
    another candidate (new evidence arrived) or a burst_end (the motion
    it was part of stopped). For the last candidate before a burst_end,
    that next event naturally *is* the burst_end, so a long multi-ping
    burst still gets its true end without special-casing "motion" vs
    "still_ping": each candidate only ever claims the span it actually
    had evidence for, so consecutive events never overlap. If nothing
    follows (the feed ended first), end_time falls back to the
    candidate's own timestamp -- duration 0, rather than guessing how
    long an unclosed event ran.
    """
    candidate = all_events[index]

    if index + 1 < len(all_events):
        return all_events[index + 1]["timestamp"]
    return candidate["timestamp"]


def run(video_stem, preferred_model=None):
    """preferred_model overrides VISION_MODEL_PREFERENCE for this run --
    this is the hook a future API/UI toggle would call through."""
    all_events = load_events(video_stem)
    results = []

    for index, event in enumerate(all_events):
        if event["kind"] != "candidate":
            continue

        frame_path = event["frame_path"]
        end_time = compute_end_time(all_events, index)
        print(f"Analyzing candidate: {Path(frame_path).name} (trigger={event['trigger']})")

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
            "timestamp": event["timestamp"],
            "end_time": end_time,
            "frame_number": event["frame_index"],
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
