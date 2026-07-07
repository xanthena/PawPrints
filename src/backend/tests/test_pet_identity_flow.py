import json
import sys
import tempfile
import unittest
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.pet_profiles import PetProfileStore
from app.query_layer.service import answer_query
from app.vision_model.prompt import build_system_prompt


PNG_BYTES = b"\x89PNG\r\n\x1a\n" + (b"identity-image" * 4)


def timeline_event(event_id, name, start):
    return {
        "event_id": event_id,
        "activities": ["playing"],
        "name_of_pet": [name],
        "start_time": start,
        "end_time": start + 2,
        "duration": 2,
        "importance": 10,
        "objects": ["cat", "toy"],
        "interaction": "toy",
        "summary": f"{name} is playing with a toy.",
        "clip_start": start - 1,
        "clip_end": start + 4,
    }


class PetIdentityFlowTests(unittest.TestCase):
    def test_prompt_no_longer_asks_the_llm_to_judge_identity(self):
        # Identity is now decided by CLIP visual similarity
        # (identity_matcher.py), not by the vision-LLM comparing reference
        # photos in its own prompt -- the LLM always reports an empty
        # name_of_pet, and reference photos are never mentioned to it.
        prompt = build_system_prompt([{"name": "Milo"}, {"name": "Luna"}])

        self.assertIn('"name_of_pet": []', prompt)
        self.assertIn('"activities": [""]', prompt)
        self.assertNotIn("reference photo", prompt.lower())
        self.assertNotIn("Milo", prompt)
        self.assertNotIn("Luna", prompt)

    def test_named_query_filters_other_cat_and_uses_name_in_answer(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profiles = root / "profiles"
            uploads = []
            for name in ("Milo", "Luna"):
                image = root / f"{name}.png"
                image.write_bytes(PNG_BYTES)
                PetProfileStore(profiles).register(name, image)
                uploads.append(image)

            timeline_root = root / "timelines"
            day = timeline_root / "2026-07-06"
            day.mkdir(parents=True)
            (day / "kitchen_final_timeline.json").write_text(
                json.dumps(
                    [
                        timeline_event(1, "Luna", 10),
                        timeline_event(2, "Milo", 30),
                    ]
                ),
                encoding="utf-8",
            )
            videos = root / "videos"
            videos.mkdir()
            (videos / "kitchen.mp4").write_bytes(b"video")

            response = answer_query(
                "Did Milo play today?",
                today="2026-07-06",
                final_timeline_dir=timeline_root,
                source_video_dir=videos,
                proof_root=root / "proofs",
                response_root=root / "responses",
                pet_profile_dir=profiles,
            )

        self.assertEqual(response["status"], "yes")
        self.assertEqual(response["match_count"], 1)
        self.assertEqual(response["evidence"][0]["name_of_pet"], ["Milo"])
        self.assertIn("Milo was observed", response["answer"])
        self.assertTrue(
            any(
                reason == "identity.name:Milo"
                for reason in response["evidence"][0]["match_reasons"]
            )
        )


if __name__ == "__main__":
    unittest.main()
