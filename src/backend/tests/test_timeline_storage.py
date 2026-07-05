import json
import os
import sys
import tempfile
import unittest
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.event_builder.main_event_tracker import run
from app.event_builder.timeline_storage import (
    daily_timeline_dir,
    final_timeline_filename,
    latest_final_timeline,
    next_final_timeline_path,
)


def vision_event():
    return {
        "frame": "frame_demo_000000_0.00s.jpg",
        "timestamp": 0.0,
        "end_time": 2.0,
        "frame_number": 0,
        "result": {
            "pet_detected": True,
            "activity": "playing",
            "confidence": 0.9,
            "objects": [{"name": "cat", "confidence": 0.9}],
            "interaction": "toy",
            "summary": "A cat is playing.",
        },
    }


class TimelineStorageTests(unittest.TestCase):
    def test_uses_video_stem_for_output_filename(self):
        self.assertEqual(
            final_timeline_filename("my_cat_video_vision.json"),
            "my_cat_video_final_timeline.json",
        )

    def test_creates_one_folder_per_date(self):
        with tempfile.TemporaryDirectory() as directory:
            first = daily_timeline_dir(directory, "2026-07-06")
            second = daily_timeline_dir(directory, "2026-07-07")

        self.assertNotEqual(first, second)
        self.assertEqual(first.name, "2026-07-06")
        self.assertEqual(second.name, "2026-07-07")

    def test_different_videos_do_not_overwrite_each_other(self):
        with tempfile.TemporaryDirectory() as directory:
            first = next_final_timeline_path(
                "first_vision.json", directory, "2026-07-06"
            )
            first.write_text("[]", encoding="utf-8")
            second = next_final_timeline_path(
                "second_vision.json", directory, "2026-07-06"
            )

        self.assertEqual(first.name, "first_final_timeline.json")
        self.assertEqual(second.name, "second_final_timeline.json")

    def test_repeated_video_run_gets_numeric_suffix(self):
        with tempfile.TemporaryDirectory() as directory:
            first = next_final_timeline_path(
                "cat_vision.json", directory, "2026-07-06"
            )
            first.write_text("[]", encoding="utf-8")
            second = next_final_timeline_path(
                "cat_vision.json", directory, "2026-07-06"
            )

        self.assertEqual(second.name, "cat_final_timeline_2.json")

    def test_latest_file_uses_modification_time(self):
        with tempfile.TemporaryDirectory() as directory:
            day_dir = Path(directory) / "2026-07-06"
            day_dir.mkdir()
            first = day_dir / "first_final_timeline.json"
            second = day_dir / "second_final_timeline.json"
            first.write_text("[]", encoding="utf-8")
            second.write_text("[]", encoding="utf-8")
            os.utime(first, ns=(3_000_000_000, 3_000_000_000))
            os.utime(second, ns=(4_000_000_000, 4_000_000_000))

            latest = latest_final_timeline(directory, "2026-07-06")

        self.assertEqual(latest.name, second.name)

    def test_event_builder_keeps_raw_and_never_overwrites_final(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            vision_json = root / "demo_vision.json"
            raw_content = json.dumps([vision_event()])
            vision_json.write_text(raw_content, encoding="utf-8")
            output_root = root / "final_timeline"

            _, _, first_output = run(
                "demo",
                input_file=vision_json,
                final_timeline_dir=output_root,
                run_date="2026-07-06",
            )
            _, _, second_output = run(
                "demo",
                input_file=vision_json,
                final_timeline_dir=output_root,
                run_date="2026-07-06",
            )

            self.assertEqual(vision_json.read_text(encoding="utf-8"), raw_content)
            self.assertTrue(first_output.is_file())
            self.assertTrue(second_output.is_file())
            self.assertNotEqual(first_output, second_output)
            self.assertEqual(first_output.parent.name, "2026-07-06")


if __name__ == "__main__":
    unittest.main()
