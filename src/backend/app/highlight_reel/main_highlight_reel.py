import argparse
import sys
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[2]
if __package__ in (None, ""):
    sys.path.insert(0, str(BACKEND_ROOT))
    from app.highlight_reel.paths import OUTPUT_DIR, SOURCE_VIDEO
    from app.highlight_reel.pipeline import generate_highlight_reel
    from app.highlight_reel.timeline_router import VALID_MODELS, resolve_timeline
else:
    from .paths import OUTPUT_DIR, SOURCE_VIDEO
    from .pipeline import generate_highlight_reel
    from .timeline_router import VALID_MODELS, resolve_timeline


def _parser():
    parser = argparse.ArgumentParser(
        description="Build a short, diverse pet highlight reel from a final timeline."
    )
    parser.add_argument(
        "--primary-model",
        choices=VALID_MODELS,
        help="Preferred model timeline; overrides environment configuration.",
    )
    parser.add_argument(
        "--fallback-model",
        choices=VALID_MODELS,
        help="Timeline to use when the primary artifact does not exist.",
    )
    parser.add_argument(
        "--timeline",
        type=Path,
        help="Explicit final timeline path; bypasses model-based resolution.",
    )
    parser.add_argument("--video", type=Path, default=SOURCE_VIDEO)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--max-clips", type=int, default=5)
    parser.add_argument("--max-clip-seconds", type=float, default=10.0)
    parser.add_argument("--ffmpeg", type=Path)
    return parser


def main(argv=None):
    args = _parser().parse_args(argv)
    timeline = resolve_timeline(
        primary=args.primary_model,
        fallback=args.fallback_model,
        timeline_path=args.timeline,
    )
    input_json = timeline["timeline_path"]
    reel_path, manifest_path, manifest = generate_highlight_reel(
        timeline_path=input_json,
        video_path=args.video,
        output_dir=args.output_dir,
        max_clips=args.max_clips,
        max_clip_duration=args.max_clip_seconds,
        ffmpeg_path=args.ffmpeg,
        timeline_model=timeline["model_used"],
        timeline_fell_back=timeline["fell_back"],
    )

    if timeline["model_used"]:
        print(f"Timeline model: {timeline['model_used']}")
        print(f"Timeline fallback used: {timeline['fell_back']}")
    else:
        print("Timeline model: explicit path")
    print(f"Input JSON: {input_json}")
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

