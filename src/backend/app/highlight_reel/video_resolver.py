"""Match a video-specific final timeline to its original source video."""

import re
from pathlib import Path

from .paths import DATA_DIR


SOURCE_VIDEO_DIR = DATA_DIR / "source_video"
VIDEO_EXTENSIONS = {".avi", ".m4v", ".mkv", ".mov", ".mp4", ".webm"}


def video_stem_from_timeline(timeline_path):
    """Extract the original video stem, including collision-suffixed outputs."""
    stem = Path(timeline_path).stem
    match = re.fullmatch(r"(.+)_final_timeline(?:_\d+)?", stem)
    if not match:
        raise ValueError(
            "Cannot infer the source video from timeline filename "
            f"'{Path(timeline_path).name}'. Pass --video explicitly."
        )
    return match.group(1)


def resolve_source_video(
    timeline_path,
    video_path=None,
    source_video_dir=SOURCE_VIDEO_DIR,
):
    """Resolve an explicit video or find the file matching the timeline stem."""
    if video_path is not None:
        explicit_path = Path(video_path).expanduser().resolve()
        if not explicit_path.is_file():
            raise FileNotFoundError(f"Source video does not exist: {explicit_path}")
        return explicit_path

    video_stem = video_stem_from_timeline(timeline_path)
    video_dir = Path(source_video_dir)
    matches = sorted(
        path
        for path in video_dir.iterdir()
        if path.is_file()
        and path.suffix.lower() in VIDEO_EXTENSIONS
        and path.stem == video_stem
    ) if video_dir.is_dir() else []

    if len(matches) == 1:
        return matches[0].resolve()
    if len(matches) > 1:
        raise RuntimeError(
            f"Multiple source videos match '{video_stem}' in {video_dir}. "
            "Pass --video explicitly."
        )
    raise FileNotFoundError(
        f"No source video matching '{video_stem}' was found in {video_dir}. "
        "Place the video there with its original filename or pass --video."
    )
