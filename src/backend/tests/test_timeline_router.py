import os
import sys
import tempfile
import unittest
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.highlight_reel.timeline_router import resolve_timeline


class TimelineRouterTests(unittest.TestCase):
    def test_selects_latest_timeline_from_requested_date(self):
        with tempfile.TemporaryDirectory() as directory:
            day_dir = Path(directory) / "2026-07-06"
            day_dir.mkdir()
            older = day_dir / "first_final_timeline.json"
            newer = day_dir / "second_final_timeline.json"
            older.write_text("[]", encoding="utf-8")
            newer.write_text("[]", encoding="utf-8")
            os.utime(older, ns=(1_000_000_000, 1_000_000_000))
            os.utime(newer, ns=(2_000_000_000, 2_000_000_000))

            outcome = resolve_timeline(
                final_timeline_dir=directory,
                run_date="2026-07-06",
            )

        self.assertEqual(outcome["timeline_path"].name, newer.name)
        self.assertEqual(outcome["timeline_date"], "2026-07-06")
        self.assertEqual(outcome["selection"], "latest_for_date")

    def test_explicit_timeline_bypasses_daily_lookup(self):
        with tempfile.TemporaryDirectory() as directory:
            timeline = Path(directory) / "final_timeline_custom.json"
            timeline.write_text("[]", encoding="utf-8")
            outcome = resolve_timeline(
                timeline_path=timeline,
                final_timeline_dir=Path(directory) / "missing",
            )

        self.assertEqual(outcome["timeline_path"].name, timeline.name)
        self.assertIsNone(outcome["timeline_date"])
        self.assertEqual(outcome["selection"], "explicit")

    def test_missing_daily_folder_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(FileNotFoundError):
                resolve_timeline(
                    final_timeline_dir=directory,
                    run_date="2026-07-06",
                )


if __name__ == "__main__":
    unittest.main()
