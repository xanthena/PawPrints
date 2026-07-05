"""Date-partitioned, non-overwriting paths for highlight reel artifacts."""

from pathlib import Path

from app.event_builder.timeline_storage import date_folder_name

from .paths import OUTPUT_DIR


def daily_highlight_dir(output_dir=OUTPUT_DIR, run_date=None):
    """Return the highlight output directory for one local calendar day."""
    return Path(output_dir) / date_folder_name(run_date)


def next_highlight_output_paths(video_path, output_dir=OUTPUT_DIR, run_date=None):
    """Return paired MP4/manifest paths that cannot overwrite an earlier run."""
    destination = daily_highlight_dir(output_dir, run_date)
    destination.mkdir(parents=True, exist_ok=True)

    video_stem = Path(video_path).stem
    counter = 1
    while True:
        suffix = "" if counter == 1 else f"_{counter}"
        reel_path = destination / f"{video_stem}_highlight_reel{suffix}.mp4"
        manifest_path = (
            destination / f"{video_stem}_highlight_reel{suffix}_manifest.json"
        )
        if not reel_path.exists() and not manifest_path.exists():
            return reel_path, manifest_path
        counter += 1

