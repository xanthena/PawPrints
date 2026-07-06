"""Command-line entry point for querying dated pet timelines."""

import argparse
import json
import sys
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[2]
if __package__ in (None, ""):
    sys.path.insert(0, str(BACKEND_ROOT))
    from app.event_builder.timeline_storage import FINAL_TIMELINE_DIR
    from app.highlight_reel.video_resolver import SOURCE_VIDEO_DIR
    from app.query_layer.proof_storage import DEFAULT_PROOF_ROOT
    from app.query_layer.response_storage import DEFAULT_RESPONSE_ROOT
    from app.query_layer.service import answer_query
else:
    from app.event_builder.timeline_storage import FINAL_TIMELINE_DIR
    from app.highlight_reel.video_resolver import SOURCE_VIDEO_DIR
    from .proof_storage import DEFAULT_PROOF_ROOT
    from .response_storage import DEFAULT_RESPONSE_ROOT
    from .service import answer_query


def _parser():
    parser = argparse.ArgumentParser(
        description="Ask evidence-backed questions about dated pet timelines."
    )
    parser.add_argument("question", nargs="+", help="Natural-language question.")
    parser.add_argument("--start-date", help="Optional YYYY-MM-DD override.")
    parser.add_argument("--end-date", help="Optional YYYY-MM-DD override.")
    parser.add_argument(
        "--proof",
        action="store_true",
        help="Create one temporary proof MP4 from all matching ranges.",
    )
    parser.add_argument(
        "--timeline-root",
        type=Path,
        default=FINAL_TIMELINE_DIR,
        help="Root containing YYYY-MM-DD final timeline folders.",
    )
    parser.add_argument(
        "--video-dir",
        type=Path,
        default=SOURCE_VIDEO_DIR,
        help="Folder containing original source videos.",
    )
    parser.add_argument(
        "--proof-root",
        type=Path,
        default=DEFAULT_PROOF_ROOT,
        help="Managed temporary proof folder.",
    )
    parser.add_argument(
        "--response-root",
        type=Path,
        default=DEFAULT_RESPONSE_ROOT,
        help="Root for dated proof/non-proof response JSON folders.",
    )
    parser.add_argument(
        "--no-save-response",
        action="store_true",
        help="Print the response without adding it to the dated response archive.",
    )
    parser.add_argument("--proof-ttl-hours", type=float, default=24)
    parser.add_argument("--ffmpeg", type=Path)
    parser.add_argument(
        "--output-json",
        type=Path,
        help="Optionally save an additional copy at an explicit path.",
    )
    return parser


def main(argv=None):
    args = _parser().parse_args(argv)
    response = answer_query(
        " ".join(args.question),
        start_date=args.start_date,
        end_date=args.end_date,
        include_proof=args.proof,
        final_timeline_dir=args.timeline_root,
        source_video_dir=args.video_dir,
        proof_root=args.proof_root,
        proof_ttl_hours=args.proof_ttl_hours,
        ffmpeg_path=args.ffmpeg,
        response_root=args.response_root,
        persist_response=not args.no_save_response,
    )
    output = json.dumps(response, indent=4, ensure_ascii=False)
    print(output)

    if args.output_json:
        output_path = args.output_json.expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = output_path.with_name(f".{output_path.name}.tmp")
        temporary.write_text(output, encoding="utf-8")
        temporary.replace(output_path)


if __name__ == "__main__":
    main()
