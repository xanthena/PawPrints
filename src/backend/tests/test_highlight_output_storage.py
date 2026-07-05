import sys
import tempfile
import unittest
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.highlight_reel.output_storage import (
    daily_highlight_dir,
    next_highlight_output_paths,
)


class HighlightOutputStorageTests(unittest.TestCase):
    def test_uses_current_run_date_folder(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = daily_highlight_dir(directory, "2026-07-06")

        self.assertEqual(destination.name, "2026-07-06")

    def test_uses_video_name_for_reel_and_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            reel, manifest = next_highlight_output_paths(
                "my_cat.mp4",
                output_dir=directory,
                run_date="2026-07-06",
            )

        self.assertEqual(reel.name, "my_cat_highlight_reel.mp4")
        self.assertEqual(manifest.name, "my_cat_highlight_reel_manifest.json")
        self.assertEqual(reel.parent.name, "2026-07-06")
        self.assertEqual(reel.parent, manifest.parent)

    def test_repeated_run_advances_both_paths_without_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            first_reel, first_manifest = next_highlight_output_paths(
                "my_cat.mp4",
                output_dir=directory,
                run_date="2026-07-06",
            )
            first_reel.write_bytes(b"video")
            first_manifest.write_text("{}", encoding="utf-8")

            second_reel, second_manifest = next_highlight_output_paths(
                "my_cat.mp4",
                output_dir=directory,
                run_date="2026-07-06",
            )

        self.assertEqual(second_reel.name, "my_cat_highlight_reel_2.mp4")
        self.assertEqual(
            second_manifest.name,
            "my_cat_highlight_reel_2_manifest.json",
        )

    def test_existing_manifest_alone_reserves_run_number(self):
        with tempfile.TemporaryDirectory() as directory:
            _, first_manifest = next_highlight_output_paths(
                "my_cat.mp4",
                output_dir=directory,
                run_date="2026-07-06",
            )
            first_manifest.write_text("{}", encoding="utf-8")

            second_reel, _ = next_highlight_output_paths(
                "my_cat.mp4",
                output_dir=directory,
                run_date="2026-07-06",
            )

        self.assertEqual(second_reel.name, "my_cat_highlight_reel_2.mp4")


if __name__ == "__main__":
    unittest.main()
