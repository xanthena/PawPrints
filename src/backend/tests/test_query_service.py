import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch


BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.query_layer.service import answer_query


def timeline_event(event_id, activity, start, end, summary, objects=None):
    return {
        "event_id": event_id,
        "activity": activity,
        "start_time": start,
        "end_time": end,
        "duration": end - start,
        "importance": 6,
        "objects": objects or ["cat"],
        "interaction": "bowl" if activity == "eating" else "",
        "summary": summary,
        "clip_start": max(0, start - 5),
        "clip_end": end + 5,
    }


def write_timeline(root, date_value, video_stem, events):
    day = Path(root) / date_value
    day.mkdir(parents=True, exist_ok=True)
    path = day / f"{video_stem}_final_timeline.json"
    path.write_text(json.dumps(events), encoding="utf-8")
    return path


class QueryServiceTests(unittest.TestCase):
    def test_yes_answer_contains_exact_source_and_timestamp_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            timelines = root / "timelines"
            videos = root / "videos"
            proofs = root / "proofs"
            videos.mkdir()
            video = videos / "kitchen.mp4"
            video.write_bytes(b"video")
            timeline = write_timeline(
                timelines,
                "2026-07-06",
                "kitchen",
                [
                    timeline_event(1, "eating", 20, 28, "A black cat is eating from a bowl."),
                    timeline_event(2, "eating", 90, 100, "The cat returned to its food bowl."),
                ],
            )

            response = answer_query(
                "Did my cat eat today?",
                today="2026-07-06",
                final_timeline_dir=timelines,
                source_video_dir=videos,
                proof_root=proofs,
            )

            self.assertEqual(response["status"], "yes")
            self.assertEqual(response["match_count"], 2)
            self.assertEqual(response["total_duration"], 18.0)
            self.assertIn("twice", response["answer"])
            self.assertEqual(response["proof"]["status"], "not_requested")
            first = response["evidence"][0]
            self.assertEqual(first["source_json_file"], timeline.name)
            self.assertEqual(first["source_json_path"], str(timeline.resolve()))
            self.assertEqual(first["source_video_name"], video.name)
            self.assertEqual(first["source_video_path"], str(video.resolve()))
            self.assertEqual(first["event_start_timestamp"], "00:00:20.000")
            self.assertEqual(first["clip_start_timestamp"], "00:00:15.000")
            self.assertEqual(first["clip_duration"], 18.0)

    def test_distinguishes_no_match_from_no_data(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            timelines = root / "timelines"
            videos = root / "videos"
            videos.mkdir()
            (videos / "kitchen.mp4").write_bytes(b"video")
            write_timeline(
                timelines,
                "2026-07-06",
                "kitchen",
                [timeline_event(1, "sleeping", 0, 10, "A cat is sleeping.")],
            )

            no_match = answer_query(
                "Did my cat eat today?",
                today="2026-07-06",
                final_timeline_dir=timelines,
                source_video_dir=videos,
            )
            no_data = answer_query(
                "Did my cat eat today?",
                today="2026-07-07",
                final_timeline_dir=timelines,
                source_video_dir=videos,
            )

        self.assertEqual(no_match["status"], "no")
        self.assertEqual(no_data["status"], "no_data")

    def test_queries_multiple_days(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            timelines = root / "timelines"
            videos = root / "videos"
            videos.mkdir()
            (videos / "kitchen.mp4").write_bytes(b"video")
            for date_value in ("2026-07-05", "2026-07-06"):
                write_timeline(
                    timelines,
                    date_value,
                    "kitchen",
                    [timeline_event(1, "jumping", 10, 12, "A cat is jumping.")],
                )

            response = answer_query(
                "Did my cat jump from 2026-07-05 to 2026-07-06?",
                final_timeline_dir=timelines,
                source_video_dir=videos,
            )

        self.assertEqual(response["status"], "yes")
        self.assertEqual(response["match_count"], 2)
        self.assertEqual(response["available_dates"], ["2026-07-05", "2026-07-06"])

    def test_requested_proof_stitches_multiple_ranges(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            timelines = root / "timelines"
            videos = root / "videos"
            proofs = root / "proofs"
            videos.mkdir()
            (videos / "kitchen.mp4").write_bytes(b"video")
            write_timeline(
                timelines,
                "2026-07-06",
                "kitchen",
                [
                    timeline_event(1, "eating", 20, 28, "A cat is eating."),
                    timeline_event(2, "eating", 90, 100, "A cat is eating again."),
                ],
            )

            def fake_render(segments, output_path, ffmpeg_path=None):
                output = Path(output_path)
                output.write_bytes(b"proof")
                return output

            with patch(
                "app.query_layer.service.render_proof_video",
                side_effect=fake_render,
            ):
                response = answer_query(
                    "Did my cat eat today?",
                    today="2026-07-06",
                    include_proof=True,
                    final_timeline_dir=timelines,
                    source_video_dir=videos,
                    proof_root=proofs,
                    now=datetime(2026, 7, 6, 12, tzinfo=timezone.utc),
                )

            self.assertEqual(response["proof"]["status"], "created")
            self.assertTrue(response["proof"]["stitched"])
            self.assertEqual(response["proof"]["segment_count"], 2)
            self.assertEqual(response["proof"]["total_duration"], 38.0)
            self.assertEqual(
                [item["proof_segment"] for item in response["evidence"]],
                [1, 2],
            )
            self.assertTrue(Path(response["proof"]["video_path"]).is_file())

    def test_missing_video_keeps_answer_but_marks_proof_unavailable(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            timelines = root / "timelines"
            videos = root / "videos"
            videos.mkdir()
            write_timeline(
                timelines,
                "2026-07-06",
                "kitchen",
                [timeline_event(1, "eating", 20, 28, "A cat is eating.")],
            )

            response = answer_query(
                "Did my cat eat today?",
                today="2026-07-06",
                include_proof=True,
                final_timeline_dir=timelines,
                source_video_dir=videos,
                proof_root=root / "proofs",
            )

        self.assertEqual(response["status"], "yes")
        self.assertEqual(response["proof"]["status"], "not_available")


if __name__ == "__main__":
    unittest.main()
