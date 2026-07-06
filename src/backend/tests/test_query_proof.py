import os
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.query_layer.proof_renderer import merge_evidence_ranges
from app.query_layer.proof_storage import (
    cleanup_expired_proofs,
    create_proof_artifact,
)


def evidence(video_path, start, end, date_value="2026-07-06"):
    return {
        "date": date_value,
        "source_video_path": str(video_path),
        "clip_start_seconds": start,
        "clip_end_seconds": end,
    }


class QueryProofTests(unittest.TestCase):
    def test_merges_overlapping_ranges_from_same_video(self):
        with tempfile.TemporaryDirectory() as directory:
            video = Path(directory) / "cat.mp4"
            items = [
                evidence(video, 10, 20),
                evidence(video, 18, 30),
                evidence(video, 50, 60),
            ]
            segments = merge_evidence_ranges(items)

        self.assertEqual(len(segments), 2)
        self.assertEqual((segments[0].clip_start, segments[0].clip_end), (10, 30))
        self.assertEqual(segments[0].evidence_indices, (0, 1))

    def test_does_not_merge_different_videos_or_dates(self):
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first.mp4"
            second = Path(directory) / "second.mp4"
            segments = merge_evidence_ranges(
                [
                    evidence(first, 10, 20, "2026-07-05"),
                    evidence(first, 10, 20, "2026-07-06"),
                    evidence(second, 10, 20, "2026-07-06"),
                ]
            )

        self.assertEqual(len(segments), 3)

    def test_artifact_path_is_unique_and_dated(self):
        with tempfile.TemporaryDirectory() as directory:
            now = datetime(2026, 7, 6, 12, tzinfo=timezone.utc)
            first = create_proof_artifact(directory, now=now)
            second = create_proof_artifact(directory, now=now)

        self.assertNotEqual(first.video_path, second.video_path)
        self.assertEqual(first.video_path.parent.name, "2026-07-06")
        self.assertTrue(first.video_path.name.endswith("_query_proof.mp4"))

    def test_cleanup_removes_only_expired_managed_proofs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            day = root / "2026-07-05"
            day.mkdir()
            expired = day / "old_query_proof.mp4"
            current = day / "new_query_proof.mp4"
            unrelated = day / "keep.mp4"
            for path in (expired, current, unrelated):
                path.write_bytes(b"video")

            now = datetime(2026, 7, 6, 12, tzinfo=timezone.utc)
            old_timestamp = now.timestamp() - (25 * 3600)
            new_timestamp = now.timestamp() - 60
            os.utime(expired, (old_timestamp, old_timestamp))
            os.utime(current, (new_timestamp, new_timestamp))
            os.utime(unrelated, (old_timestamp, old_timestamp))

            deleted = cleanup_expired_proofs(root, max_age_hours=24, now=now)

            self.assertEqual(deleted, [expired])
            self.assertFalse(expired.exists())
            self.assertTrue(current.exists())
            self.assertTrue(unrelated.exists())


if __name__ == "__main__":
    unittest.main()
