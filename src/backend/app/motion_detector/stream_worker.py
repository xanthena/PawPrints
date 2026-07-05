import argparse
import json
from pathlib import Path

import cv2 as cv

from .candidate_queue import CandidateFrameQueue
from .frame_diff import FrameDiffDetector

REPO_ROOT = Path(__file__).resolve().parents[4]
SRC_ROOT = REPO_ROOT / "src"
EVENTS_DIR = SRC_ROOT / "data" / "events"
FRAMES_DIR = SRC_ROOT / "data" / "frames"
DEFAULT_VIDEO = SRC_ROOT / "data" / "cat_inbag.mp4"

SMALL_WIDTH = 320
SAMPLE_INTERVAL_SEC = 0.5
COOLDOWN_SEC = 4.0
STILL_PING_INTERVAL_SEC = 300.0

# Riz's vision-model testing settled on 768x432 (landscape) as a size that
# works well across models. Our source video is portrait, so forcing exact
# 768x432 would either stretch the image or letterbox away most of the
# frame. Capping the long edge at 768 instead preserves aspect ratio and
# lands on the same pixel budget (roughly 330k px) for either orientation.
VISION_LONG_EDGE = 768


def resize_keep_aspect(frame, target_width=SMALL_WIDTH):
    h, w = frame.shape[:2]
    scale = target_width / w
    return cv.resize(frame, (target_width, int(h * scale)))


def resize_for_vision_model(frame, long_edge=VISION_LONG_EDGE):
    h, w = frame.shape[:2]
    if w >= h:
        new_w, new_h = long_edge, int(h * (long_edge / w))
    else:
        new_h, new_w = long_edge, int(w * (long_edge / h))
    return cv.resize(frame, (new_w, new_h))


def stream_events(video_source, cooldown_sec=COOLDOWN_SEC, still_ping_interval_sec=STILL_PING_INTERVAL_SEC):
    """
    Reads video_source sequentially -- a finished file today, a live
    camera/RTSP URL tomorrow, cv.VideoCapture treats both identically --
    and yields one event dict per motion burst start/continuation
    ("candidate", trigger "motion"), a coarse check-in during sustained
    stillness ("candidate", trigger "still_ping"), or a burst end. Never
    assumes a known total length, so the same loop works unchanged for a
    finished file or a feed that never ends.
    """
    vid = cv.VideoCapture(str(video_source))
    if not vid.isOpened():
        raise RuntimeError(f"Could not open video source: {video_source}")

    fps = int(vid.get(cv.CAP_PROP_FPS)) or 30
    sample_every = max(1, int(fps * SAMPLE_INTERVAL_SEC))

    detector = FrameDiffDetector(use_contours=True)
    queue = CandidateFrameQueue(
        detector,
        cooldown_sec=cooldown_sec,
        still_ping_interval_sec=still_ping_interval_sec,
    )

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

            event = queue.observe(frame, small_frame, timestamp, frame_index)
            if event is not None:
                yield event

            frame_index += 1
    finally:
        vid.release()


def persist_event(event, out_dir, video_stem):
    """
    Metadata for every event (candidate or burst_end) goes to
    out_dir/events.jsonl. Candidate frame images are resized for the
    vision model and written into FRAMES_DIR directly, using Riz's
    frame_<number>_<timestamp>s.jpg naming convention (prefixed with the
    video stem, since frame_index restarts at 0 for every video and
    would otherwise collide across footages sharing that flat directory)
    -- that's what his vision-model pipeline scans, so no extra glue is
    needed to make our candidates visible to it.
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    if event["kind"] == "candidate":
        FRAMES_DIR.mkdir(parents=True, exist_ok=True)
        frame = event.pop("frame")
        resized = resize_for_vision_model(frame)
        frame_name = f"frame_{video_stem}_{event['frame_index']:06d}_{event['timestamp']:.2f}s.jpg"
        frame_path = FRAMES_DIR / frame_name
        cv.imwrite(str(frame_path), resized)
        event["frame_path"] = str(frame_path)

    with open(out_dir / "events.jsonl", "a") as f:
        f.write(json.dumps(event) + "\n")

    return event


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("video_path", nargs="?", default=str(DEFAULT_VIDEO))
    parser.add_argument("--cooldown", type=float, default=COOLDOWN_SEC)
    parser.add_argument("--still-ping-interval", type=float, default=STILL_PING_INTERVAL_SEC)
    args = parser.parse_args()

    video_stem = Path(args.video_path).stem
    out_dir = EVENTS_DIR / video_stem

    counts = {"candidate": 0, "burst_end": 0}
    for event in stream_events(
        args.video_path,
        cooldown_sec=args.cooldown,
        still_ping_interval_sec=args.still_ping_interval,
    ):
        persist_event(event, out_dir, video_stem)
        counts[event["kind"]] += 1
        trigger = f" ({event['trigger']})" if event["kind"] == "candidate" else ""
        print(f"{event['kind']}{trigger}: frame {event['frame_index']} @ {event['timestamp']:.2f}s")

    print(f"{counts['candidate']} candidate(s), {counts['burst_end']} burst_end(s) written to {out_dir}")
