import sys
import unittest
from pathlib import Path
from unittest.mock import patch


BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.vision_model import model_router


class _FakeProfile:
    def __init__(self, name):
        self.name = name
        self.image_paths = (Path("unused.png"),)


class ModelRouterIdentityTests(unittest.TestCase):
    def test_registered_pet_names_reflects_the_actual_clip_match(self):
        # Regression test: registered_pet_names used to be every
        # registered pet's name, deduped from their reference photos,
        # regardless of what was actually in the candidate frame -- real
        # filtering only ever happened inside the LLM's own (unreliable)
        # guess. Now identity_matcher.match_identity() is the source of
        # truth, and analyze() must pass its result through untouched.
        profiles = [_FakeProfile("Coffee"), _FakeProfile("Nachos")]

        with patch.object(
            model_router.identity_matcher, "match_identity", return_value=["Coffee"]
        ) as mock_match, patch.object(
            model_router, "_call", return_value='{"name_of_pet": []}'
        ):
            outcome = model_router.analyze(
                "candidate.jpg",
                allowed_dir="/tmp",
                primary="gemini",
                fallback=None,
                pet_profiles=profiles,
            )

        mock_match.assert_called_once()
        self.assertEqual(outcome["registered_pet_names"], ["Coffee"])

    def test_no_match_returns_empty_registered_pet_names_even_with_profiles(self):
        profiles = [_FakeProfile("Coffee"), _FakeProfile("Nachos")]

        with patch.object(
            model_router.identity_matcher, "match_identity", return_value=[]
        ), patch.object(model_router, "_call", return_value='{"name_of_pet": []}'):
            outcome = model_router.analyze(
                "candidate.jpg",
                allowed_dir="/tmp",
                primary="gemini",
                fallback=None,
                pet_profiles=profiles,
            )

        self.assertEqual(outcome["registered_pet_names"], [])


if __name__ == "__main__":
    unittest.main()
