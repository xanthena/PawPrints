import sys
import unittest
from datetime import date
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.query_layer.intent_parser import parse_query_intent
from app.query_layer.matcher import match_event
from app.query_layer.models import TimelineEvent


def timeline_event(activity, summary, objects=None, interaction=""):
    return TimelineEvent(
        event_date=date(2026, 7, 6),
        source_json=Path("kitchen_final_timeline.json"),
        source_video=Path("kitchen.mp4"),
        source_video_error=None,
        data={
            "event_id": 1,
            "activity": activity,
            "start_time": 10,
            "end_time": 18,
            "duration": 8,
            "clip_start": 5,
            "clip_end": 23,
            "objects": objects or ["cat"],
            "interaction": interaction,
            "summary": summary,
        },
    )


class QueryIntentMatcherTests(unittest.TestCase):
    def test_matches_eating_activity(self):
        intent = parse_query_intent("Did my cat eat today?")
        event = timeline_event("eating", "A cat is eating from a bowl.")
        self.assertIsNotNone(match_event(event, intent))

    def test_matches_running_synonym(self):
        intent = parse_query_intent("Was my cat running around?")
        event = timeline_event("running", "A cat ran across the room.")
        self.assertIsNotNone(match_event(event, intent))

    def test_near_sofa_requires_movement_and_sofa_evidence(self):
        intent = parse_query_intent("Did my cat come near the sofa?")
        matching = timeline_event(
            "walking",
            "A cat walked near the couch.",
            objects=["cat", "sofa"],
        )
        unrelated = timeline_event(
            "sleeping",
            "A cat slept on the sofa.",
            objects=["cat", "sofa"],
        )
        self.assertIsNotNone(match_event(matching, intent))
        self.assertIsNone(match_event(unrelated, intent))

    def test_object_alias_matches_couch_as_sofa(self):
        intent = parse_query_intent("Was my cat on the sofa?")
        event = timeline_event(
            "sitting",
            "A cat is sitting on a couch.",
            objects=["cat", "couch"],
        )
        self.assertIsNotNone(match_event(event, intent))

    def test_unknown_question_is_unsupported(self):
        intent = parse_query_intent("Was everything okay?")
        self.assertFalse(intent.supported)


if __name__ == "__main__":
    unittest.main()
