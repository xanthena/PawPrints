import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch


BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.query_layer.path_utils import REPO_ROOT
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


def query_paths(root):
    return {
        "final_timeline_dir": root / "timelines",
        "source_video_dir": root / "videos",
        "proof_root": root / "proofs",
        "response_root": root / "responses",
    }


class QueryServiceTests(unittest.TestCase):
    def test_yes_answer_uses_reduced_relative_path_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = query_paths(root)
            paths["source_video_dir"].mkdir()
            video = paths["source_video_dir"] / "kitchen.mp4"
            video.write_bytes(b"video")
            timeline = write_timeline(
                paths["final_timeline_dir"],
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
                **paths,
            )

            self.assertEqual(response["status"], "yes")
            self.assertEqual(response["match_count"], 2)
            self.assertEqual(response["total_duration"], 18.0)
            self.assertIn("twice", response["answer"])
            self.assertEqual(
                response["proof"],
                {"requested": False, "status": "not_requested", "error": ""},
            )
            first = response["evidence"][0]
            for removed_field in (
                "importance",
                "source_json_file",
                "source_video_name",
                "event_start_seconds",
                "event_end_seconds",
                "event_start_timestamp",
                "event_end_timestamp",
            ):
                self.assertNotIn(removed_field, first)
            self.assertFalse(Path(first["source_json_path"]).is_absolute())
            self.assertFalse(Path(first["source_video_path"]).is_absolute())
            self.assertTrue(first["source_json_path"].endswith(timeline.name))
            self.assertTrue(first["source_video_path"].endswith(video.name))
            self.assertEqual(first["clip_start_timestamp"], "00:00:15.000")
            self.assertEqual(first["clip_duration"], 18.0)
            self.assertFalse(Path(response["timeline_files"][0]).is_absolute())

            saved = list(
                (paths["response_root"] / "2026-07-06" / "proof_not_requested").glob("*.json")
            )
            self.assertEqual(len(saved), 1)
            self.assertEqual(json.loads(saved[0].read_text()), response)

    def test_distinguishes_no_match_from_no_data(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = query_paths(root)
            paths["source_video_dir"].mkdir()
            (paths["source_video_dir"] / "kitchen.mp4").write_bytes(b"video")
            write_timeline(
                paths["final_timeline_dir"],
                "2026-07-06",
                "kitchen",
                [timeline_event(1, "sleeping", 0, 10, "A cat is sleeping.")],
            )

            no_match = answer_query(
                "Did my cat eat today?",
                today="2026-07-06",
                **paths,
            )
            no_data = answer_query(
                "Did my cat eat today?",
                today="2026-07-07",
                **paths,
            )

        self.assertEqual(no_match["status"], "no")
        self.assertEqual(no_data["status"], "no_data")

    def test_queries_multiple_days(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = query_paths(root)
            paths["source_video_dir"].mkdir()
            (paths["source_video_dir"] / "kitchen.mp4").write_bytes(b"video")
            for date_value in ("2026-07-05", "2026-07-06"):
                write_timeline(
                    paths["final_timeline_dir"],
                    date_value,
                    "kitchen",
                    [timeline_event(1, "jumping", 10, 12, "A cat is jumping.")],
                )

            response = answer_query(
                "Did my cat jump from 2026-07-05 to 2026-07-06?",
                **paths,
            )

        self.assertEqual(response["status"], "yes")
        self.assertEqual(response["match_count"], 2)
        self.assertEqual(response["available_dates"], ["2026-07-05", "2026-07-06"])

    def test_requested_proof_uses_reduced_contract_and_proof_folder(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = query_paths(root)
            paths["source_video_dir"].mkdir()
            (paths["source_video_dir"] / "kitchen.mp4").write_bytes(b"video")
            write_timeline(
                paths["final_timeline_dir"],
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
                    now=datetime(2026, 7, 6, 12, tzinfo=timezone.utc),
                    **paths,
                )

            proof = response["proof"]
            self.assertEqual(proof["status"], "created")
            self.assertEqual(proof["error"], "")
            self.assertTrue(proof["stitched"])
            self.assertEqual(proof["segment_count"], 2)
            self.assertNotIn("video_name", proof)
            self.assertFalse(Path(proof["video_path"]).is_absolute())
            self.assertEqual(
                [item["proof_segment"] for item in response["evidence"]],
                [1, 2],
            )
            for segment in proof["segments"]:
                self.assertNotIn("source_video_path", segment)
                self.assertNotIn("evidence_indices", segment)

            proof_file = (REPO_ROOT / proof["video_path"]).resolve()
            self.assertTrue(proof_file.is_file())
            saved = list(
                (paths["response_root"] / "2026-07-06" / "proof_requested").glob("*.json")
            )
            self.assertEqual(len(saved), 1)

    def test_missing_video_keeps_answer_and_puts_message_in_error(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = query_paths(root)
            paths["source_video_dir"].mkdir()
            write_timeline(
                paths["final_timeline_dir"],
                "2026-07-06",
                "kitchen",
                [timeline_event(1, "eating", 20, 28, "A cat is eating.")],
            )

            response = answer_query(
                "Did my cat eat today?",
                today="2026-07-06",
                include_proof=True,
                **paths,
            )

        self.assertEqual(response["status"], "yes")
        self.assertEqual(response["proof"]["status"], "not_available")
        self.assertTrue(response["proof"]["error"])
        self.assertNotIn("reason", response["proof"])


if __name__ == "__main__":
    unittest.main()
