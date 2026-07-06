import sys
import tempfile
import unittest
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.highlight_reel.video_resolver import (
    resolve_source_video,
    video_stem_from_timeline,
)


class HighlightVideoResolverTests(unittest.TestCase):
    def test_extracts_video_stem_from_normal_and_collision_names(self):
        self.assertEqual(
            video_stem_from_timeline("my_cat_final_timeline.json"),
            "my_cat",
        )
        self.assertEqual(
            video_stem_from_timeline("my_cat_final_timeline_3.json"),
            "my_cat",
        )

    def test_finds_matching_source_video(self):
        with tempfile.TemporaryDirectory() as directory:
            video = Path(directory) / "my_cat.mp4"
            video.write_bytes(b"video")
            resolved = resolve_source_video(
                "my_cat_final_timeline.json",
                source_video_dir=directory,
            )

        self.assertEqual(resolved.name, video.name)

    def test_explicit_video_bypasses_filename_inference(self):
        with tempfile.TemporaryDirectory() as directory:
            video = Path(directory) / "custom-name.mp4"
            video.write_bytes(b"video")
            resolved = resolve_source_video(
                "unrecognized.json",
                video_path=video,
                source_video_dir=Path(directory) / "missing",
            )

        self.assertEqual(resolved.name, video.name)

    def test_missing_match_requests_explicit_video(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(FileNotFoundError):
                resolve_source_video(
                    "my_cat_final_timeline.json",
                    source_video_dir=directory,
                )


if __name__ == "__main__":
    unittest.main()
