import json
import sys
import tempfile
import unittest
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.query_layer.date_parser import parse_date_scope
from app.query_layer.timeline_repository import load_timeline_range


def event(activity):
    return {
        "event_id": 1,
        "activity": activity,
        "start_time": 0,
        "end_time": 5,
        "duration": 5,
        "objects": ["cat"],
        "interaction": "",
        "summary": f"A cat is {activity}.",
        "clip_start": 0,
        "clip_end": 10,
    }


class QueryRepositoryTests(unittest.TestCase):
    def test_keeps_distinct_videos_and_latest_version_of_each(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            timelines = root / "timelines"
            videos = root / "videos"
            day = timelines / "2026-07-06"
            day.mkdir(parents=True)
            videos.mkdir()
            (videos / "kitchen.mp4").write_bytes(b"video")
            (videos / "garden.mp4").write_bytes(b"video")

            (day / "kitchen_final_timeline.json").write_text(
                json.dumps([event("eating")]), encoding="utf-8"
            )
            (day / "kitchen_final_timeline_2.json").write_text(
                json.dumps([event("jumping")]), encoding="utf-8"
            )
            (day / "garden_final_timeline.json").write_text(
                json.dumps([event("running")]), encoding="utf-8"
            )

            result = load_timeline_range(
                parse_date_scope("today", today="2026-07-06"),
                final_timeline_dir=timelines,
                source_video_dir=videos,
            )

        self.assertEqual(len(result.timeline_files), 2)
        self.assertEqual({item.activity for item in result.events}, {"jumping", "running"})
        self.assertTrue(all(item.source_video is not None for item in result.events))

    def test_loads_multiple_days_and_reports_missing_dates(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            timelines = root / "timelines"
            videos = root / "videos"
            videos.mkdir()
            (videos / "kitchen.mp4").write_bytes(b"video")
            day = timelines / "2026-07-05"
            day.mkdir(parents=True)
            (day / "kitchen_final_timeline.json").write_text(
                json.dumps([event("eating")]), encoding="utf-8"
            )

            result = load_timeline_range(
                parse_date_scope(
                    "range",
                    start_date="2026-07-05",
                    end_date="2026-07-06",
                ),
                final_timeline_dir=timelines,
                source_video_dir=videos,
            )

        self.assertEqual([item.isoformat() for item in result.available_dates], ["2026-07-05"])
        self.assertEqual([item.isoformat() for item in result.missing_dates], ["2026-07-06"])

    def test_missing_video_keeps_queryable_event_with_warning_field(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            timelines = root / "timelines"
            videos = root / "videos"
            day = timelines / "2026-07-06"
            day.mkdir(parents=True)
            videos.mkdir()
            (day / "kitchen_final_timeline.json").write_text(
                json.dumps([event("eating")]), encoding="utf-8"
            )

            result = load_timeline_range(
                parse_date_scope("today", today="2026-07-06"),
                final_timeline_dir=timelines,
                source_video_dir=videos,
            )

        self.assertEqual(len(result.events), 1)
        self.assertIsNone(result.events[0].source_video)
        self.assertIn("No source video", result.events[0].source_video_error)


if __name__ == "__main__":
    unittest.main()
