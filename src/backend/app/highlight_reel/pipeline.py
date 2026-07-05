import json
from datetime import datetime, timezone
from pathlib import Path

from .output_storage import next_highlight_output_paths
from .renderer import render_highlight_reel
from .selector import load_timeline, select_highlights


def generate_highlight_reel(
    timeline_path,
    video_path,
    output_dir,
    max_clips=5,
    max_clip_duration=10.0,
    ffmpeg_path=None,
    timeline_date=None,
    timeline_selection=None,
    run_date=None,
):
    """Select highlights, render a dated reel, and write its manifest."""
    timeline = Path(timeline_path).resolve()
    video = Path(video_path).resolve()
    destination = Path(output_dir).resolve()

    events = load_timeline(timeline)
    clips = select_highlights(
        events,
        max_clips=max_clips,
        max_clip_duration=max_clip_duration,
    )
    if not clips:
        raise ValueError("The timeline contains no events to include in a reel.")

    reel_destination, manifest_path = next_highlight_output_paths(
        video,
        output_dir=destination,
        run_date=run_date,
    )
    reel_path = render_highlight_reel(
        video,
        clips,
        reel_destination,
        ffmpeg_path=ffmpeg_path,
    )

    manifest = {
        "timeline_file": str(timeline),
        "timeline_date": timeline_date,
        "timeline_selection": timeline_selection,
        "source_video": str(video),
        "output_video": str(reel_path),
        "highlight_date": reel_path.parent.name,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "selection_strategy": "relative importance plus diversity; no fixed importance threshold",
        "max_clips": max_clips,
        "max_clip_duration": max_clip_duration,
        "selected_clip_count": len(clips),
        "reel_duration": round(sum(clip.duration for clip in clips), 3),
        "clips": [clip.to_dict() for clip in clips],
    }
    temporary_manifest = manifest_path.with_name(f".{manifest_path.name}.tmp")
    temporary_manifest.write_text(
        json.dumps(manifest, indent=4, ensure_ascii=False),
        encoding="utf-8",
    )
    temporary_manifest.replace(manifest_path)
    return reel_path, manifest_path, manifest
