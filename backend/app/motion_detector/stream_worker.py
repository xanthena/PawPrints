import argparse
import json
from pathlib import Path

import cv2 as cv

from .candidate_queue import CandidateFrameQueue
from .frame_diff import FrameDiffDetector

REPO_ROOT = Path(__file__).resolve().parents[3]
CANDIDATES_DIR = REPO_ROOT / "data" / "candidates"
DEFAULT_VIDEO = REPO_ROOT / "data" / "cat_inbag.mp4"

SMALL_WIDTH = 320
SAMPLE_INTERVAL_SEC = 0.5
COOLDOWN_SEC = 4.0


def resize_keep_aspect(frame, target_width=SMALL_WIDTH):
    h, w = frame.shape[:2]
    scale = target_width / w
    return cv.resize(frame, (target_width, int(h * scale)))


def stream_candidates(video_source, cooldown_sec=COOLDOWN_SEC):
    """
    Reads video_source sequentially -- a finished file today, a live
    camera/RTSP URL tomorrow, cv.VideoCapture treats both identically --
    and yields one candidate dict per representative motion event, as
    soon as it's found. Never assumes a known total length, so the same
    loop works unchanged for a finished file or a feed that never ends.
    """
    vid = cv.VideoCapture(str(video_source))
    if not vid.isOpened():
        raise RuntimeError(f"Could not open video source: {video_source}")

    fps = int(vid.get(cv.CAP_PROP_FPS)) or 30
    sample_every = max(1, int(fps * SAMPLE_INTERVAL_SEC))

    detector = FrameDiffDetector(use_contours=True)
    queue = CandidateFrameQueue(detector, cooldown_sec=cooldown_sec)

    frame_index = 0
    try:
        while True:
            ret, frame = vid.read()
            if not ret:
                break

            if frame_index % sample_every != 0:
                frame_index += 1
                continue

            timestamp = frame_index / fps
            small_frame = resize_keep_aspect(frame)

            candidate = queue.observe(frame, small_frame, timestamp, frame_index)
            if candidate is not None:
                yield candidate

            frame_index += 1
    finally:
        vid.release()


def persist_candidate(candidate, out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)

    frame = candidate.pop("frame")
    frame_path = out_dir / f"frame_{candidate['frame_index']}.jpg"
    cv.imwrite(str(frame_path), frame)
    candidate["frame_path"] = str(frame_path)

    with open(out_dir / "candidates.jsonl", "a") as f:
        f.write(json.dumps(candidate) + "\n")

    return candidate


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("video_path", nargs="?", default=str(DEFAULT_VIDEO))
    parser.add_argument("--cooldown", type=float, default=COOLDOWN_SEC)
    args = parser.parse_args()

    out_dir = CANDIDATES_DIR / Path(args.video_path).stem

    count = 0
    for candidate in stream_candidates(args.video_path, cooldown_sec=args.cooldown):
        persist_candidate(candidate, out_dir)
        count += 1
        print(f"candidate {count}: frame {candidate['frame_index']} @ {candidate['timestamp']:.2f}s")

    print(f"{count} candidate(s) written to {out_dir}")
