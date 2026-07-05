import argparse
import json
import time
from datetime import datetime
from pathlib import Path

import cv2 as cv

from .frame_diff import FrameDiffDetector
from .mog2 import MOG2Detector

REPO_ROOT = Path(__file__).resolve().parents[3]
RESULTS_DIR = REPO_ROOT / "results"
DEFAULT_VIDEO = REPO_ROOT / "data" / "cat_inbag.mp4"

SMALL_WIDTH = 320
SAMPLE_INTERVAL_SEC = 0.5


def build_detectors():
    return {
        "framediff_full": FrameDiffDetector(use_contours=False),
        "framediff_contours_full": FrameDiffDetector(use_contours=True),
        "mog2_full": MOG2Detector(use_contours=False),
        "mog2_contours_full": MOG2Detector(use_contours=True),
        "framediff_small": FrameDiffDetector(use_contours=False),
        "framediff_contours_small": FrameDiffDetector(use_contours=True),
        "mog2_small": MOG2Detector(use_contours=False),
        "mog2_contours_small": MOG2Detector(use_contours=True),
    }


def resize_keep_aspect(frame, target_width=SMALL_WIDTH):
    h, w = frame.shape[:2]
    scale = target_width / w
    return cv.resize(frame, (target_width, int(h * scale)))


def run(video_path):
    vid = cv.VideoCapture(str(video_path))
    if not vid.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    fps = int(vid.get(cv.CAP_PROP_FPS)) or 30
    sample_every = max(1, int(fps * SAMPLE_INTERVAL_SEC))

    detectors = build_detectors()
    logs = {name: [] for name in detectors}

    frame_index = 0
    run_start = time.perf_counter()

    while True:
        ret, frame = vid.read()
        if not ret:
            break

        if frame_index % sample_every != 0:
            frame_index += 1
            continue

        timestamp = frame_index / fps
        small_frame = resize_keep_aspect(frame)

        for name, detector in detectors.items():
            target_frame = small_frame if name.endswith("_small") else frame

            start = time.perf_counter()
            result = detector.detect(target_frame)
            elapsed = time.perf_counter() - start

            logs[name].append({
                "frame_index": frame_index,
                "timestamp": timestamp,
                "elapsed": elapsed,
                **result,
            })

        frame_index += 1

    total_run_time = time.perf_counter() - run_start
    vid.release()

    meta = {"video_path": str(video_path), "fps": fps, "total_run_time_sec": total_run_time}
    return logs, meta


def write_results(logs, meta):
    run_dir = RESULTS_DIR / f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    run_dir.mkdir(parents=True, exist_ok=True)

    summary = {"_meta": meta}

    for name, entries in logs.items():
        motion_flagged = sum(1 for e in entries if e["motion"])
        avg_elapsed = sum(e["elapsed"] for e in entries) / len(entries) if entries else 0.0

        summary[name] = {
            "motion_flagged_frames": motion_flagged,
            "sampled_frames": len(entries),
            "avg_processing_time_sec": avg_elapsed,
        }

        with open(run_dir / f"{name}.json", "w") as f:
            json.dump(entries, f, indent=2)

    with open(run_dir / "summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    return run_dir, summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("video_path", nargs="?", default=str(DEFAULT_VIDEO))
    args = parser.parse_args()

    logs, meta = run(args.video_path)
    run_dir, summary = write_results(logs, meta)

    print(f"Results written to {run_dir}")
    print(json.dumps(summary, indent=2))
