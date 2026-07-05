import sys
import unittest
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.highlight_reel.selector import load_timeline, select_highlights
from app.highlight_reel.timeline_router import timeline_path_for


class FinalTimelineCompatibilityTests(unittest.TestCase):
    def test_gemini_and_qwen_timelines_both_select_a_short_reel(self):
        for model in ("gemini", "qwen"):
            with self.subTest(model=model):
                timeline_path = timeline_path_for(model)
                events = load_timeline(timeline_path)
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
