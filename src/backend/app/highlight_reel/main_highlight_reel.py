import argparse
import sys
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[2]
if __package__ in (None, ""):
    sys.path.insert(0, str(BACKEND_ROOT))
    from app.highlight_reel.paths import JSONS_DIR, OUTPUT_DIR, SOURCE_VIDEO
    from app.highlight_reel.pipeline import generate_highlight_reel
else:
    from .paths import JSONS_DIR, OUTPUT_DIR, SOURCE_VIDEO
    from .pipeline import generate_highlight_reel


# User-facing choice: keep cloud selected for now. Change to "local" for Qwen.
INPUT_MODE = "cloud"
INPUT_OPTIONS = {
    "local": JSONS_DIR / "final_timeline_qwen.json",
    "cloud": JSONS_DIR / "final_timeline_gemini.json",
}


def get_input_json(input_mode):
    try:
        return INPUT_OPTIONS[input_mode]
    except KeyError as error:
        valid_modes = ", ".join(sorted(INPUT_OPTIONS))
        raise ValueError(
            f"Unknown input mode '{input_mode}'. Use one of: {valid_modes}."
        ) from error


def _parser():
    parser = argparse.ArgumentParser(
        description="Build a short, diverse pet highlight reel from a final timeline."
    )
    parser.add_argument(
        "--input-mode",
        choices=sorted(INPUT_OPTIONS),
        default=INPUT_MODE,
        help=f"Timeline provider (default: {INPUT_MODE}).",
    )
    parser.add_argument("--video", type=Path, default=SOURCE_VIDEO)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--max-clips", type=int, default=5)
    parser.add_argument("--max-clip-seconds", type=float, default=10.0)
    parser.add_argument("--ffmpeg", type=Path)
    return parser


def main(argv=None):
    args = _parser().parse_args(argv)
    input_json = get_input_json(args.input_mode)
    reel_path, manifest_path, manifest = generate_highlight_reel(
        timeline_path=input_json,
        video_path=args.video,
        output_dir=args.output_dir,
        max_clips=args.max_clips,
        max_clip_duration=args.max_clip_seconds,
        ffmpeg_path=args.ffmpeg,
    )

    print(f"Input mode: {args.input_mode}")
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

