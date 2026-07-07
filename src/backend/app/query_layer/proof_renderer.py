"""Cut evidence ranges from one or more source videos into standalone clips."""

import tempfile
from pathlib import Path

from app.media_tools import resolve_ffmpeg, run_ffmpeg

from .models import ProofSegment


NORMALIZE_FILTER = (
    "scale=1280:720:force_original_aspect_ratio=decrease,"
    "pad=1280:720:(ow-iw)/2:(oh-ih)/2:color=black,fps=30"
)


def merge_evidence_ranges(evidence):
    """Merge overlaps while preserving the incoming relevance-first order."""
    candidates = []
    for index, item in enumerate(evidence):
        source_path = item.get("source_video_path")
        if not source_path:
            continue
        start = float(item["clip_start_seconds"])
        end = float(item["clip_end_seconds"])
        if end <= start:
            continue
        candidates.append(
            {
                "date": item["date"],
                "source": Path(source_path).resolve(),
                "start": start,
                "end": end,
                "evidence_indices": [index],
                "relevance_score": float(item.get("relevance_score", 0.0)),
            }
        )

    merged = []
    for candidate in candidates:
        overlap_indices = [
            index
            for index, existing in enumerate(merged)
            if existing["date"] == candidate["date"]
            and existing["source"] == candidate["source"]
            and candidate["start"] <= existing["end"]
            and existing["start"] <= candidate["end"]
        ]
        if not overlap_indices:
            merged.append(candidate)
            continue

        primary = merged[overlap_indices[0]]
        primary["start"] = min(primary["start"], candidate["start"])
        primary["end"] = max(primary["end"], candidate["end"])
        primary["evidence_indices"].extend(candidate["evidence_indices"])
        primary["relevance_score"] = max(
            primary["relevance_score"],
            candidate["relevance_score"],
        )

        for overlap_index in reversed(overlap_indices[1:]):
            extra = merged.pop(overlap_index)
            primary["start"] = min(primary["start"], extra["start"])
            primary["end"] = max(primary["end"], extra["end"])
            primary["evidence_indices"].extend(extra["evidence_indices"])
            primary["relevance_score"] = max(
                primary["relevance_score"],
                extra["relevance_score"],
            )

    merged.sort(key=lambda item: min(item["evidence_indices"]))

    from datetime import date

    return [
        ProofSegment(
            event_date=date.fromisoformat(item["date"]),
            source_video=item["source"],
            clip_start=item["start"],
            clip_end=item["end"],
            evidence_indices=tuple(item["evidence_indices"]),
            relevance_score=item["relevance_score"],
        )
        for item in merged
    ]


def render_proof_clips(segments, output_dir, query_id, ffmpeg_path=None):
    """Normalize each evidence segment into its own standalone MP4.

    Each matching moment (e.g. one per day for a multi-day query) becomes
    a separate playable clip instead of one stitched-together video, so a
    caller can list/play them individually and see which day or moment
    each one came from. Returns a list of Paths in the same order as
    `segments`.

    All clips are rendered into a temp directory first and only moved
    into `output_dir` once every one has succeeded, so a failure partway
    through never leaves a partial set of proof files behind.
    """
    if not segments:
        raise ValueError("At least one proof segment is required.")

    destination_dir = Path(output_dir).resolve()
    destination_dir.mkdir(parents=True, exist_ok=True)
    ffmpeg = resolve_ffmpeg(ffmpeg_path)

    with tempfile.TemporaryDirectory(
        prefix="query-proof-",
        dir=destination_dir,
    ) as temporary_directory:
        temporary = Path(temporary_directory)
        rendered_segments = []

        for index, segment in enumerate(segments, start=1):
            if not segment.source_video.is_file():
                raise FileNotFoundError(
                    f"Proof source video does not exist: {segment.source_video}"
                )
            clip_path = temporary / f"segment_{index:03d}.mp4"
            run_ffmpeg(
                [
                    ffmpeg,
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-y",
                    "-ss",
                    f"{segment.clip_start:.3f}",
                    "-t",
                    f"{segment.duration:.3f}",
                    "-i",
                    str(segment.source_video),
                    "-map",
                    "0:v:0",
                    "-vf",
                    NORMALIZE_FILTER,
                    "-an",
                    "-c:v",
                    "libx264",
                    "-preset",
                    "fast",
                    "-crf",
                    "21",
                    "-pix_fmt",
                    "yuv420p",
                    "-avoid_negative_ts",
                    "make_zero",
                    str(clip_path),
                ],
                f"creating proof segment {index}",
            )
            rendered_segments.append(clip_path)

        destinations = []
        for index, clip_path in enumerate(rendered_segments, start=1):
            destination = destination_dir / f"{query_id}_query_proof_{index}.mp4"
            clip_path.replace(destination)
            destinations.append(destination)

    return destinations
