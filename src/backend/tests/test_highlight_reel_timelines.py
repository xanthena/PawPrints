import sys
import unittest
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.event_builder.timeline_storage import JSONS_DIR
from app.highlight_reel.selector import load_timeline, select_highlights


class FinalTimelineCompatibilityTests(unittest.TestCase):
    def test_existing_gemini_and_qwen_timelines_remain_compatible(self):
        for filename in ("final_timeline_gemini.json", "final_timeline_qwen.json"):
            with self.subTest(filename=filename):
                events = load_timeline(JSONS_DIR / filename)
                clips = select_highlights(events, max_clips=5, max_clip_duration=10)
                selected_ids = {clip.event["event_id"] for clip in clips}
                best_score = max(event["importance"] for event in events)
                best_ids = {
                    event["event_id"]
                    for event in events
                    if event["importance"] == best_score
                }

                self.assertEqual(len(clips), 5)
                self.assertTrue(selected_ids & best_ids)
                self.assertTrue(all(0 < clip.duration <= 10 for clip in clips))
                self.assertEqual(clips, sorted(clips, key=lambda clip: clip.clip_start))


if __name__ == "__main__":
    unittest.main()
