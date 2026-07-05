"""Resolve the newest final timeline from today's dated folder."""

from pathlib import Path

from app.event_builder.timeline_storage import (
    FINAL_TIMELINE_DIR,
    date_folder_name,
    latest_final_timeline,
)


def resolve_timeline(
    timeline_path=None,
    final_timeline_dir=FINAL_TIMELINE_DIR,
    run_date=None,
):
    """Resolve an explicit timeline or today's most recently written one."""
    if timeline_path is not None:
        explicit_path = Path(timeline_path).expanduser().resolve()
        if not explicit_path.is_file():
            raise FileNotFoundError(f"Timeline JSON does not exist: {explicit_path}")
        return {
            "timeline_path": explicit_path,
            "timeline_date": None,
            "selection": "explicit",
        }

    timeline = latest_final_timeline(
        final_timeline_dir=final_timeline_dir,
        run_date=run_date,
    )
    return {
        "timeline_path": timeline.resolve(),
        "timeline_date": date_folder_name(run_date),
        "selection": "latest_for_date",
    }
