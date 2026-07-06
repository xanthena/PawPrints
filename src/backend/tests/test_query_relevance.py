import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.query_layer.matcher import rank_matches
from app.query_layer.models import QueryMatch, TimelineEvent
from app.query_layer.proof_renderer import merge_evidence_ranges


def match(video, event_id, start, score, reasons):
    event = TimelineEvent(
        event_date=date(2026, 7, 6),
        source_json=Path("cat_final_timeline.json"),
        source_video=video,
        source_video_error=None,
        data={
            "event_id": event_id,
            "activities": ["playing"],
            "start_time": start,
            "end_time": start + 2,
            "duration": 2,
            "clip_start": start - 1,
            "clip_end": start + 4,
        },
    )
    return QueryMatch(event=event, score=score, reasons=tuple(reasons))


class QueryRelevanceTests(unittest.TestCase):
    def test_rank_matches_puts_stronger_later_event_first(self):
        video = Path("cat.mp4")
        early = match(video, 1, 10, 0.7, ["activity.playing.activity:playing"])
        later = match(
            video,
            2,
            50,
            1.3,
            [
                "activity.playing.activity:playing",
                "activity.playing.summary:playing",
            ],
        )

        ranked = rank_matches([early, later])

        self.assertEqual([item.event.data["event_id"] for item in ranked], [2, 1])

    def test_merged_segments_keep_relevance_order_instead_of_time_order(self):
        with tempfile.TemporaryDirectory() as directory:
            video = Path(directory) / "cat.mp4"
            evidence = [
                {
                    "date": "2026-07-06",
                    "source_video_path": str(video),
                    "clip_start_seconds": 49,
                    "clip_end_seconds": 54,
                    "relevance_score": 1.3,
                },
                {
                    "date": "2026-07-06",
                    "source_video_path": str(video),
                    "clip_start_seconds": 9,
                    "clip_end_seconds": 14,
                    "relevance_score": 0.7,
                },
            ]

            segments = merge_evidence_ranges(evidence)

        self.assertEqual([item.clip_start for item in segments], [49, 9])
        self.assertEqual([item.relevance_score for item in segments], [1.3, 0.7])

    def test_overlap_merge_keeps_highest_relevance_score(self):
        with tempfile.TemporaryDirectory() as directory:
            video = Path(directory) / "cat.mp4"
            evidence = [
                {
                    "date": "2026-07-06",
                    "source_video_path": str(video),
                    "clip_start_seconds": 10,
                    "clip_end_seconds": 15,
                    "relevance_score": 1.4,
                },
                {
                    "date": "2026-07-06",
                    "source_video_path": str(video),
                    "clip_start_seconds": 14,
                    "clip_end_seconds": 18,
                    "relevance_score": 0.8,
                },
            ]

            segments = merge_evidence_ranges(evidence)

        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0].clip_start, 10)
        self.assertEqual(segments[0].clip_end, 18)
        self.assertEqual(segments[0].relevance_score, 1.4)


if __name__ == "__main__":
    unittest.main()
