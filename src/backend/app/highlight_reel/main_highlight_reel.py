import argparse
import sys
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[2]
if __package__ in (None, ""):
    sys.path.insert(0, str(BACKEND_ROOT))
    from app.highlight_reel.paths import OUTPUT_DIR
    from app.highlight_reel.pipeline import generate_highlight_reel
    from app.highlight_reel.timeline_router import resolve_timeline
    from app.highlight_reel.video_resolver import resolve_source_video
else:
    from .paths import OUTPUT_DIR
    from .pipeline import generate_highlight_reel
    from .timeline_router import resolve_timeline
    from .video_resolver import resolve_source_video


def _parser():
    parser = argparse.ArgumentParser(
        description=(
            "Build a short, diverse pet highlight reel from today's newest "
            "final timeline."
        )
    )
    parser.add_argument(
        "--timeline",
        type=Path,
        help="Explicit final timeline path; bypasses today's latest-file lookup.",
    )
    parser.add_argument(
        "--video",
        type=Path,
        help=(
            "Explicit source video. By default it is matched to the selected "
            "timeline filename in src/data/source_video."
        ),
    )
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--max-clips", type=int, default=5)
    parser.add_argument("--max-clip-seconds", type=float, default=10.0)
    parser.add_argument("--ffmpeg", type=Path)
    return parser


def main(argv=None):
    args = _parser().parse_args(argv)
    timeline = resolve_timeline(timeline_path=args.timeline)
    input_json = timeline["timeline_path"]
    source_video = resolve_source_video(input_json, video_path=args.video)
    reel_path, manifest_path, manifest = generate_highlight_reel(
        timeline_path=input_json,
        video_path=source_video,
        output_dir=args.output_dir,
        max_clips=args.max_clips,
        max_clip_duration=args.max_clip_seconds,
        ffmpeg_path=args.ffmpeg,
        timeline_date=timeline["timeline_date"],
        timeline_selection=timeline["selection"],
    )

    print(f"Timeline selection: {timeline['selection']}")
    if timeline["timeline_date"]:
        print(f"Timeline date: {timeline['timeline_date']}")
    print(f"Input JSON: {input_json}")
    print(f"Source video: {source_video}")
    print(f"Selected clips: {manifest['selected_clip_count']}")
    for clip in manifest["clips"]:
        print(
            f"  event {clip['event_id']}: {clip['activity']} "
            f"(importance {clip['importance']}, "
            f"{clip['clip_start']:.1f}s-{clip['clip_end']:.1f}s)"
        )
    print(f"Reel: {reel_path}")
    print(f"Manifest: {manifest_path}")


if __name__ == "__main__":
    main()

