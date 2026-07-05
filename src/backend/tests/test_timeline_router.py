import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.highlight_reel.timeline_router import resolve_timeline, timeline_path_for


class TimelineRouterTests(unittest.TestCase):
    def test_defaults_to_gemini_and_exposes_model_used(self):
        with patch.dict(os.environ, {}, clear=True):
            outcome = resolve_timeline()

        self.assertEqual(outcome["model_used"], "gemini")
        self.assertFalse(outcome["fell_back"])
        self.assertEqual(outcome["timeline_path"].name, "final_timeline_gemini.json")

    def test_explicit_model_overrides_environment(self):
        environment = {
            "HIGHLIGHT_MODEL_PRIMARY": "gemini",
            "HIGHLIGHT_MODEL_FALLBACK": "gemini",
        }
        with patch.dict(os.environ, environment, clear=True):
            outcome = resolve_timeline(primary="qwen", fallback="qwen")

        self.assertEqual(outcome["model_used"], "qwen")
        self.assertFalse(outcome["fell_back"])

    def test_highlight_environment_overrides_upstream_vision_environment(self):
        environment = {
            "VISION_MODEL_PRIMARY": "gemini",
            "VISION_MODEL_FALLBACK": "gemini",
            "HIGHLIGHT_MODEL_PRIMARY": "qwen",
            "HIGHLIGHT_MODEL_FALLBACK": "qwen",
        }
        with patch.dict(os.environ, environment, clear=True):
            outcome = resolve_timeline()

        self.assertEqual(outcome["model_used"], "qwen")

    def test_missing_primary_uses_configured_fallback_once(self):
        with tempfile.TemporaryDirectory() as directory:
            jsons_dir = Path(directory)
            timeline_path_for("qwen", jsons_dir).write_text("[]", encoding="utf-8")
            outcome = resolve_timeline(
                primary="claude",
                fallback="qwen",
                jsons_dir=jsons_dir,
            )

        self.assertEqual(outcome["model_used"], "qwen")
        self.assertTrue(outcome["fell_back"])

    def test_explicit_timeline_bypasses_model_routing(self):
        with tempfile.TemporaryDirectory() as directory:
            timeline = Path(directory) / "final_timeline_custom.json"
            timeline.write_text("[]", encoding="utf-8")
            outcome = resolve_timeline(
                primary="not-a-model",
                timeline_path=timeline,
            )

        self.assertIsNone(outcome["model_used"])
        self.assertFalse(outcome["fell_back"])

    def test_invalid_model_is_rejected(self):
        with self.assertRaises(ValueError):
            resolve_timeline(primary="not-a-model")


if __name__ == "__main__":
    unittest.main()
