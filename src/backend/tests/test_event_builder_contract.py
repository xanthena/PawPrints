import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.event_builder.event_pipeline import run_event_pipeline


class _FakeProfile:
    def __init__(self, name):
        self.name = name


class EventBuilderContractTests(unittest.TestCase):
    def test_keeps_multiple_activities_on_one_event_and_uses_tight_padding(self):
        raw = [
            {
                "frame": "frame_demo_000300_10.00s.jpg",
                "timestamp": 10,
                "end_time": 14,
                "result": {
                    "pet_detected": True,
                    "activity": "grooming, sleeping",
                    "activity_confidence": 0.97,
                    "name_of_pet": ["Milo"],
                    "objects": [{"name": "kitten", "confidence": 0.9}],
                    "interaction": "",
                    "summary": "Milo is grooming while another cat sleeps.",
                },
            }
        ]

        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "input.json"
            output_path = Path(directory) / "output.json"
            input_path.write_text(json.dumps(raw), encoding="utf-8")
            # clean_results() checks name_of_pet against the actually
            # registered roster (see its _registered_pet_names) rather
            # than trusting the model's own claim -- fake that roster
            # here instead of depending on whatever's really registered
            # on disk, which would make this test order/state dependent.
            with patch(
                "app.event_builder.clean_results.list_pet_profiles",
                return_value=[_FakeProfile("Milo")],
            ):
                events = run_event_pipeline(input_path, output_path)

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["activities"], ["grooming", "sleeping"])
        self.assertNotIn("activity", events[0])
        self.assertEqual(events[0]["name_of_pet"], ["Milo"])
        self.assertEqual(events[0]["clip_start"], 9)
        self.assertEqual(events[0]["clip_end"], 16)

    def test_clip_start_is_clamped_to_zero(self):
        raw = [
            {
                "frame": "frame_demo_000000_0.00s.jpg",
                "timestamp": 0.25,
                "end_time": 1,
                "result": {
                    "pet_detected": True,
                    "activities": ["playing"],
                    "confidence": 0.8,
                    "objects": [],
                    "interaction": "",
                    "summary": "A cat is playing.",
                },
            }
        ]

        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "input.json"
            output_path = Path(directory) / "output.json"
            input_path.write_text(json.dumps(raw), encoding="utf-8")
            events = run_event_pipeline(input_path, output_path)

        self.assertEqual(events[0]["clip_start"], 0)
        self.assertEqual(events[0]["clip_end"], 3)


if __name__ == "__main__":
    unittest.main()
