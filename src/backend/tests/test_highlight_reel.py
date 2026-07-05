import sys
import unittest
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.highlight_reel.selector import select_highlights


def event(
    event_id,
    activity,
    importance,
    timestamp,
    interaction="",
    objects=None,
    duration=0,
):
    return {
        "event_id": event_id,
        "activity": activity,
        "start_time": timestamp,
        "end_time": timestamp + duration,
        "importance": importance,
        "objects": objects or ["cat"],
        "interaction": interaction,
        "summary": f"Event {event_id}",
        "clip_start": max(0, timestamp - 5),
        "clip_end": timestamp + duration + 5,
    }


class HighlightSelectorTests(unittest.TestCase):
    def test_uses_best_available_scores_without_absolute_threshold(self):
        events = [
            event(1, "playing", 6, 10, "toy", ["cat", "toy"]),
            event(2, "eating", 5, 40, "bowl", ["cat", "bowl"]),
            event(3, "looking_out", 4, 80, "window", ["cat", "window"]),
        ]

        clips = select_highlights(events, max_clips=3)

        self.assertEqual({clip.event["event_id"] for clip in clips}, {1, 2, 3})
        self.assertEqual(len(clips), 3)

    def test_diversity_prevents_repetitive_playing_clips_from_dominating(self):
        events = [
            event(1, "playing", 10, 10, "toy", ["cat", "toy"]),
            event(2, "playing", 9, 12, "toy", ["cat", "toy"]),
            event(3, "playing", 8, 80, "toy", ["cat", "toy"]),
            event(4, "eating", 7, 45, "bowl", ["cat", "bowl"]),
            event(5, "looking_out", 6, 120, "window", ["cat", "window"]),
            event(6, "approaching_camera", 5, 160, "camera", ["cat", "camera"]),
        ]

        clips = select_highlights(events, max_clips=4)
        activities = {clip.event["activity"] for clip in clips}

        self.assertIn(1, {clip.event["event_id"] for clip in clips})
        self.assertGreaterEqual(len(activities), 3)
        self.assertLessEqual(
            sum(clip.event["activity"] == "playing" for clip in clips),
            2,
        )

    def test_caps_long_events_and_centers_point_events(self):
        events = [
            event(1, "playing", 6, 20, "toy", duration=30),
            event(2, "eating", 5, 70, "bowl"),
        ]

        clips = select_highlights(events, max_clips=2, max_clip_duration=8)
        by_id = {clip.event["event_id"]: clip for clip in clips}

        self.assertAlmostEqual(by_id[1].duration, 8)
        self.assertAlmostEqual(by_id[1].clip_start, 20)
        self.assertAlmostEqual(by_id[2].duration, 8)
        self.assertAlmostEqual(by_id[2].clip_start, 66)
        self.assertAlmostEqual(by_id[2].clip_end, 74)

    def test_empty_timeline_returns_no_clips(self):
        self.assertEqual(select_highlights([]), [])


if __name__ == "__main__":
    unittest.main()
