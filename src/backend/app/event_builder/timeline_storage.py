"""Shared naming and date-partitioning for final event timelines."""

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
