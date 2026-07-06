"""Load dated final timelines and enrich events with their source footage."""

import json
import re
from datetime import date
from pathlib import Path

from app.event_builder.timeline_storage import FINAL_TIMELINE_DIR
from app.highlight_reel.video_resolver import SOURCE_VIDEO_DIR, resolve_source_video

from .date_parser import iter_dates
from .models import RepositoryResult, TimelineEvent


TIMELINE_NAME_PATTERN = re.compile(r"^(.+)_final_timeline(?:_(\d+))?\.json$")


def _timeline_identity(path):
    match = TIMELINE_NAME_PATTERN.fullmatch(Path(path).name)
    if not match:
        return Path(path).stem, 1
    return match.group(1), int(match.group(2) or 1)


def select_latest_version_per_video(files):
    """Keep distinct videos but avoid counting reprocessed footage twice."""
    selected = {}
    for path in files:
        video_stem, version = _timeline_identity(path)
        key = (version, path.stat().st_mtime_ns, path.name)
        previous = selected.get(video_stem)
        if previous is None or key > previous[0]:
            selected[video_stem] = (key, path)
    return sorted(item[1] for item in selected.values())


def _load_json_list(path):
    with path.open("r", encoding="utf-8") as file:
        payload = json.load(file)
    if not isinstance(payload, list):
        raise ValueError("final timeline must contain a JSON list")
    return payload


def load_timeline_range(
    scope,
    final_timeline_dir=FINAL_TIMELINE_DIR,
    source_video_dir=SOURCE_VIDEO_DIR,
):
    """Load all distinct-video timelines in an inclusive date range."""
    result = RepositoryResult()
    timeline_root = Path(final_timeline_dir)

    for requested_date in iter_dates(scope):
        day_dir = timeline_root / requested_date.isoformat()
        candidates = sorted(day_dir.glob("*.json")) if day_dir.is_dir() else []
        if not candidates:
            result.missing_dates.append(requested_date)
            continue

        loaded_for_date = False
        for timeline_path in select_latest_version_per_video(candidates):
            try:
                raw_events = _load_json_list(timeline_path)
            except (OSError, ValueError, json.JSONDecodeError) as error:
                result.warnings.append(f"Skipped {timeline_path}: {error}")
                continue

            try:
                source_video = resolve_source_video(
                    timeline_path,
                    source_video_dir=source_video_dir,
                )
                source_video_error = None
            except (FileNotFoundError, RuntimeError, ValueError) as error:
                source_video = None
                source_video_error = str(error)

            valid_events = 0
            for index, raw_event in enumerate(raw_events, start=1):
                if not isinstance(raw_event, dict):
                    result.warnings.append(
                        f"Skipped event {index} in {timeline_path}: event must be an object"
                    )
                    continue
                result.events.append(
                    TimelineEvent(
                        event_date=requested_date,
                        source_json=timeline_path.resolve(),
                        source_video=source_video,
                        source_video_error=source_video_error,
                        data=raw_event,
                    )
                )
                valid_events += 1

            result.timeline_files.append(timeline_path.resolve())
            loaded_for_date = loaded_for_date or valid_events > 0 or not raw_events

        if loaded_for_date:
            result.available_dates.append(requested_date)
        else:
            result.missing_dates.append(requested_date)

    result.events.sort(
        key=lambda event: (
            event.event_date,
            event.source_json.name,
            event.start_time,
            event.data.get("event_id", 0),
        )
    )
    return result
