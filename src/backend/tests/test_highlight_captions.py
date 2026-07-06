import sys
import unittest
from pathlib import Path
import tempfile


BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.highlight_reel.captions import caption_for_event, event_activities


from app.highlight_reel.renderer import FONT_CANDIDATES, _wrapped_caption, build_caption_filter
class HighlightCaptionTests(unittest.TestCase):
    def test_personalizes_summary_with_single_registered_name(self):
        caption = caption_for_event(
            {
                "activities": ["playing"],
                "name_of_pet": ["Milo"],
                "summary": "A small tabby kitten is playing with a ball.",
            }
        )

        self.assertEqual(caption, "Milo is playing with a ball")

    def test_personalizes_two_cat_summary(self):
        caption = caption_for_event(
            {
                "activities": ["eating"],
                "name_of_pet": ["Milo", "Luna"],
                "summary": "Two cats are eating from separate bowls.",
            }
        )

        self.assertEqual(caption, "Milo and Luna are eating from separate bowls")

    def test_uses_activity_fallback_and_legacy_activity(self):
        self.assertEqual(
            caption_for_event({"activity": "looking_out", "summary": ""}),
            "A cat — looking out",
        )
        self.assertEqual(event_activities({"activity": "playing"}), ["playing"])

    def test_caption_is_short(self):
        caption = caption_for_event(
            {
                "activities": ["playing"],
                "summary": "A cat " + ("enthusiastically runs around the room " * 8),
            }
        )

        self.assertLessEqual(len(caption), 92)
        self.assertTrue(caption.endswith("…"))
    def test_rendered_caption_has_closed_caption_brackets(self):
        self.assertEqual(_wrapped_caption("Milo is playing"), "[Milo is playing]")
        self.assertEqual(_wrapped_caption("one two", width=6), "[one\ntwo]")

    def test_drawtext_filter_uses_textfile_and_cinematic_style(self):
        with tempfile.TemporaryDirectory() as directory:
            caption_file = Path(directory) / "caption.txt"
            caption_file.write_text("Milo is playing", encoding="utf-8")
            video_filter = build_caption_filter(caption_file)

        self.assertIn("drawtext", video_filter)
        self.assertIn("textfile=", video_filter)
        self.assertIn("fontcolor=white", video_filter)
        self.assertIn("fontsize=h/26", video_filter)
        self.assertIn("line_spacing=2", video_filter)
        self.assertIn("text_align=C", video_filter)
        self.assertIn("y=h-text_h-h*0.045", video_filter)
        self.assertIn("box=1", video_filter)
        self.assertIn("boxcolor=black@0.24", video_filter)
        self.assertIn("boxborderw=5", video_filter)
        self.assertNotIn(":borderw=", video_filter)
        self.assertNotIn("bordercolor=", video_filter)
        self.assertNotIn("shadowx=", video_filter)
        self.assertNotIn("shadowcolor=", video_filter)
        self.assertIn("x=(w-text_w)/2", video_filter)

    def test_default_caption_fonts_are_not_italic(self):
        font_names = [path.name.lower() for path in FONT_CANDIDATES]
        self.assertFalse(any("italic" in name for name in font_names))
        self.assertFalse(any("oblique" in name for name in font_names))
        self.assertNotIn("ariali.ttf", font_names)
        self.assertNotIn("segoeuii.ttf", font_names)


if __name__ == "__main__":
    unittest.main()



