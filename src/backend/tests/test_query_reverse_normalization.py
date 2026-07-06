import sys
import unittest
from datetime import date
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.query_layer.intent_parser import parse_query_intent
from app.query_layer.matcher import match_event
from app.query_layer.models import TimelineEvent


def event(activity, summary, objects=None, interaction=""):
    return TimelineEvent(
        event_date=date(2026, 7, 6),
        source_json=Path("cat_final_timeline.json"),
        source_video=Path("cat.mp4"),
        source_video_error=None,
        data={
            "event_id": 1,
            "activity": activity,
            "start_time": 10,
            "end_time": 15,
            "duration": 5,
            "clip_start": 5,
            "clip_end": 20,
            "objects": objects or ["cat"],
            "interaction": interaction,
            "summary": summary,
        },
    )


class ReverseQueryNormalizationTests(unittest.TestCase):
    def test_played_question_matches_toy_interaction_and_object(self):
        intent = parse_query_intent("Has my cat played today?")
        candidate = event(
            "jumping",
            "A cat jumps across the floor.",
            objects=["cat", "toy"],
            interaction="toy",
        )

        match = match_event(candidate, intent)

        self.assertIsNotNone(match)
        self.assertTrue(any("interaction:toy" in reason for reason in match.reasons))
        self.assertTrue(any("objects:toy" in reason for reason in match.reasons))

    def test_play_query_matches_zoomies_in_summary(self):
        intent = parse_query_intent("Did my cat play?")
        candidate = event(
            "running",
            "The cat had the zoomies and was running around the room.",
        )

        match = match_event(candidate, intent)

        self.assertIsNotNone(match)
        self.assertTrue(any("summary:zoomies" in reason for reason in match.reasons))

    def test_toying_around_is_understood_as_playing(self):
        intent = parse_query_intent("Was my cat toying around today?")
        self.assertIn("playing", intent.activities)

    def test_summary_action_can_match_when_activity_label_is_generic(self):
        intent = parse_query_intent("Did my cat eat?")
        candidate = event(
            "sitting",
            "The cat is munching food beside its bowl.",
            objects=["cat", "food"],
        )

        match = match_event(candidate, intent)

        self.assertIsNotNone(match)
        self.assertTrue(any("summary:munching" in reason for reason in match.reasons))

    def test_lone_toy_object_does_not_turn_sleeping_into_playing(self):
        intent = parse_query_intent("Did my cat play?")
        candidate = event(
            "sleeping",
            "A cat is asleep near a toy.",
            objects=["cat", "toy"],
        )

        self.assertIsNone(match_event(candidate, intent))


if __name__ == "__main__":
    unittest.main()
