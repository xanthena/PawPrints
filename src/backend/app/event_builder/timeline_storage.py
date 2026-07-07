"""Shared naming and date-partitioning for final event timelines."""

import json
from datetime import date, datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
JSONS_DIR = REPO_ROOT / "src" / "data" / "jsons"
FINAL_TIMELINE_DIR = JSONS_DIR / "final_timeline"


def date_folder_name(run_date=None):
    """Return an ISO date folder name using local time by default."""
    if run_date is None:
        resolved = datetime.now().astimezone().date()
    elif isinstance(run_date, datetime):
        resolved = run_date.date()
    elif isinstance(run_date, date):
        resolved = run_date
    else:
        try:
            resolved = date.fromisoformat(str(run_date))
        except ValueError as error:
            raise ValueError("run_date must use YYYY-MM-DD format.") from error
    return resolved.isoformat()


def daily_timeline_dir(final_timeline_dir=FINAL_TIMELINE_DIR, run_date=None):
    """Return the final-timeline directory for one local calendar day."""
    return Path(final_timeline_dir) / date_folder_name(run_date)


def video_stem_from_vision(vision_json):
    """Turn ``<video_stem>_vision.json`` into ``<video_stem>``."""
    stem = Path(vision_json).stem
    return stem[:-len("_vision")] if stem.endswith("_vision") else stem


def final_timeline_filename(vision_json):
    """Build a video-specific final timeline filename."""
    return f"{video_stem_from_vision(vision_json)}_final_timeline.json"


def next_final_timeline_path(
    vision_json,
    final_timeline_dir=FINAL_TIMELINE_DIR,
    run_date=None,
):
    """Return a new dated output path without overwriting an earlier run."""
    output_dir = daily_timeline_dir(final_timeline_dir, run_date)
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = final_timeline_filename(vision_json)
    candidate = output_dir / filename
    if not candidate.exists():
        return candidate

    stem = Path(filename).stem
    suffix = Path(filename).suffix
    counter = 2
    while True:
        candidate = output_dir / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def latest_final_timeline(
    final_timeline_dir=FINAL_TIMELINE_DIR,
    run_date=None,
):
    """Return the most recently modified final timeline for one day."""
    timeline_dir = daily_timeline_dir(final_timeline_dir, run_date)
    if not timeline_dir.is_dir():
        raise FileNotFoundError(
            f"No final timeline folder exists for {date_folder_name(run_date)}: "
            f"{timeline_dir}"
        )

    timelines = [path for path in timeline_dir.glob("*.json") if path.is_file()]
    if not timelines:
        raise FileNotFoundError(
            f"No final timeline JSON files exist for "
            f"{date_folder_name(run_date)}: {timeline_dir}"
        )

    return max(timelines, key=lambda path: (path.stat().st_mtime_ns, path.name))


def rename_pet_in_timelines(old_name, new_name, final_timeline_dir=FINAL_TIMELINE_DIR):
    """Update every already-persisted final-timeline event's name_of_pet
    field that references old_name, in place.

    A pet rename should apply to history, not just future identity
    matches -- otherwise the dashboard and query layer would keep
    showing the old name for every video analyzed before the rename,
    which reads as the rename having silently failed. This only touches
    the final timeline JSON (what the frontend and query layer actually
    read); it does not touch raw per-frame vision.json files (internal,
    not user-facing) or already-rendered highlight reel videos (the old
    name may still be burned into their captions until regenerated).

    Returns the number of individual events changed.
    """
    old_key = str(old_name).strip().casefold()
    updated_events = 0
    root = Path(final_timeline_dir)
    if not root.is_dir():
        return updated_events

    for path in root.glob("*/*.json"):
        try:
            events = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        if not isinstance(events, list):
            continue

        changed = False
        for event in events:
            if not isinstance(event, dict):
                continue
            names = event.get("name_of_pet")
            if not isinstance(names, list):
                continue
            renamed = [
                new_name if str(name).strip().casefold() == old_key else name
                for name in names
            ]
            if renamed != names:
                event["name_of_pet"] = renamed
                changed = True
                updated_events += 1

        if changed:
            path.write_text(json.dumps(events, indent=4, ensure_ascii=False), encoding="utf-8")

    return updated_events
