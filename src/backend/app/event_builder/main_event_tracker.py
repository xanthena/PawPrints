import argparse
import sys
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[2]
if __package__ in (None, ""):
    sys.path.insert(0, str(BACKEND_ROOT))
    from app.event_builder.event_pipeline import run_event_pipeline
    from app.event_builder.timeline_storage import (
        FINAL_TIMELINE_DIR,
        JSONS_DIR,
        next_final_timeline_path,
    )
else:
    from .event_pipeline import run_event_pipeline
    from .timeline_storage import (
        FINAL_TIMELINE_DIR,
        JSONS_DIR,
        next_final_timeline_path,
    )


def get_input_json(video_stem, jsons_dir=JSONS_DIR):
    """Resolve the overwrite-in-place output produced by vision_model."""
    stem = Path(video_stem).stem
    if stem.endswith("_vision"):
        stem = stem[:-len("_vision")]
    return Path(jsons_dir) / f"{stem}_vision.json"


def run(
    video_stem,
    input_file=None,
    final_timeline_dir=FINAL_TIMELINE_DIR,
    run_date=None,
):
    """Build a dated, collision-safe final timeline for one video."""
    input_json = (
        Path(input_file)
        if input_file is not None
        else get_input_json(video_stem)
    )
    if not input_json.is_file():
        raise FileNotFoundError(f"Vision JSON does not exist: {input_json}")

    output_json = next_final_timeline_path(
        input_json,
        final_timeline_dir=final_timeline_dir,
        run_date=run_date,
    )
    final_events = run_event_pipeline(input_json, output_json)
    return final_events, input_json, output_json


def _parser():
    parser = argparse.ArgumentParser(
        description="Build a dated final event timeline from vision-model JSON."
    )
    parser.add_argument(
        "video_stem",
        help="Video filename stem used by <video_stem>_vision.json.",
    )
    parser.add_argument(
        "--input",
        type=Path,
        help="Explicit vision JSON path; its filename is used for output naming.",
    )
    return parser


def main(argv=None):
    args = _parser().parse_args(argv)
    final_events, input_json, output_json = run(
        args.video_stem,
        input_file=args.input,
    )
    print(f"Input JSON: {input_json}")
    print(f"Generated {len(final_events)} events")
    print(f"Final timeline: {output_json}")


if __name__ == "__main__":
    main()
