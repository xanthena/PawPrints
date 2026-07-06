"""Public orchestration API for evidence-backed timeline questions."""

from datetime import datetime
from pathlib import Path

from app.event_builder.timeline_storage import FINAL_TIMELINE_DIR
from app.highlight_reel.video_resolver import SOURCE_VIDEO_DIR
from app.pet_profiles import DEFAULT_PROFILE_DIR, list_pet_profiles

from .answer_builder import build_answer
from .date_parser import parse_date_scope
from .intent_parser import parse_query_intent
from .matcher import find_matches, rank_matches
from .path_utils import relative_repo_path
from .proof_renderer import merge_evidence_ranges, render_proof_video
from .proof_storage import (
    DEFAULT_PROOF_ROOT,
    cleanup_expired_proofs,
    create_proof_artifact,
)
from .response_storage import DEFAULT_RESPONSE_ROOT, store_query_response
from .time_format import format_video_timestamp
from .timeline_repository import load_timeline_range


def _round_seconds(value):
    return round(float(value), 3)


def _evidence_item(match):
    event = match.event
    video = event.source_video
    return {
        "event_id": event.data.get("event_id"),
        "date": event.event_date.isoformat(),
        "activities": list(event.activities),
        "name_of_pet": list(event.pet_names),
        "summary": str(event.data.get("summary", "")),
        "objects": event.data.get("objects", []),
        "interaction": str(event.data.get("interaction", "")),
        "relevance_score": _round_seconds(match.score),
        "duration": _round_seconds(event.duration),
        "source_json_path": str(event.source_json),
        "source_video_path": str(video) if video else None,
        "source_video_error": event.source_video_error,
        "clip_start_seconds": _round_seconds(event.clip_start),
        "clip_end_seconds": _round_seconds(event.clip_end),
        "clip_start_timestamp": format_video_timestamp(event.clip_start),
        "clip_end_timestamp": format_video_timestamp(event.clip_end),
        "clip_duration": _round_seconds(event.clip_end - event.clip_start),
        "match_reasons": list(match.reasons),
        "proof_segment": None,
    }


def _proof_not_requested():
    return {
        "requested": False,
        "status": "not_requested",
        "error": "",
    }


def _build_proof(
    evidence,
    proof_root,
    proof_ttl_hours,
    ffmpeg_path,
    now,
):
    if not evidence:
        return {
            "requested": True,
            "status": "not_available",
            "error": "No matching evidence exists to render.",
        }

    segments = merge_evidence_ranges(evidence)
    if not segments:
        errors = sorted(
            {
                item["source_video_error"]
                for item in evidence
                if item.get("source_video_error")
            }
        )
        error = "No matching source video could be resolved."
        if errors:
            error = f"{error} {'; '.join(errors)}"
        return {
            "requested": True,
            "status": "not_available",
            "error": error,
        }

    for segment_number, segment in enumerate(segments, start=1):
        for evidence_index in segment.evidence_indices:
            evidence[evidence_index]["proof_segment"] = segment_number

    cleanup_expired_proofs(
        proof_root=proof_root,
        max_age_hours=proof_ttl_hours,
        now=now,
    )
    artifact = create_proof_artifact(
        proof_root=proof_root,
        ttl_hours=proof_ttl_hours,
        now=now,
    )
    try:
        proof_path = render_proof_video(
            segments,
            artifact.video_path,
            ffmpeg_path=ffmpeg_path,
        )
    except Exception as error:
        if artifact.video_path.exists():
            artifact.video_path.unlink()
        for item in evidence:
            item["proof_segment"] = None
        return {
            "requested": True,
            "status": "failed",
            "error": str(error),
        }

    unavailable_count = sum(not item.get("source_video_path") for item in evidence)
    proof_segments = []
    for segment_number, segment in enumerate(segments, start=1):
        proof_segments.append(
            {
                "segment": segment_number,
                "date": segment.event_date.isoformat(),
                "source_video_name": segment.source_video.name,
                "clip_start_seconds": _round_seconds(segment.clip_start),
                "clip_end_seconds": _round_seconds(segment.clip_end),
                "clip_start_timestamp": format_video_timestamp(segment.clip_start),
                "clip_end_timestamp": format_video_timestamp(segment.clip_end),
                "clip_duration": _round_seconds(segment.duration),
                "relevance_score": _round_seconds(segment.relevance_score),
            }
        )

    proof_error = (
        f"{unavailable_count} evidence item(s) had no resolvable source video."
        if unavailable_count
        else ""
    )
    return {
        "requested": True,
        "status": "partial" if unavailable_count else "created",
        "error": proof_error,
        "query_id": artifact.query_id,
        "video_path": str(proof_path),
        "segment_count": len(segments),
        "stitched": len(segments) > 1,
        "total_duration": _round_seconds(sum(segment.duration for segment in segments)),
        "expires_at": artifact.expires_at.isoformat(),
        "unavailable_evidence_count": unavailable_count,
        "segments": proof_segments,
    }


def _make_response_paths_relative(response):
    response["timeline_files"] = [
        relative_repo_path(path) for path in response["timeline_files"]
    ]
    for item in response["evidence"]:
        item["source_json_path"] = relative_repo_path(item["source_json_path"])
        item["source_video_path"] = relative_repo_path(item["source_video_path"])
    proof_path = response["proof"].get("video_path")
    if proof_path:
        response["proof"]["video_path"] = relative_repo_path(proof_path)
    return response


def answer_query(
    question,
    start_date=None,
    end_date=None,
    include_proof=False,
    final_timeline_dir=FINAL_TIMELINE_DIR,
    source_video_dir=SOURCE_VIDEO_DIR,
    proof_root=DEFAULT_PROOF_ROOT,
    proof_ttl_hours=24,
    pet_profile_dir=DEFAULT_PROFILE_DIR,
    ffmpeg_path=None,
    today=None,
    now=None,
    response_root=DEFAULT_RESPONSE_ROOT,
    persist_response=True,
):
    """Answer a basic timeline question, optionally render proof, and save JSON."""
    operation_now = now or datetime.now().astimezone()
    scope = parse_date_scope(
        question,
        start_date=start_date,
        end_date=end_date,
        today=today,
    )
    profiles = list_pet_profiles(pet_profile_dir)
    intent = parse_query_intent(
        question, known_pet_names=(profile.name for profile in profiles)
    )

    if not intent.supported:
        status = "unsupported"
        matches = []
        repository = None
    else:
        repository = load_timeline_range(
            scope,
            final_timeline_dir=final_timeline_dir,
            source_video_dir=source_video_dir,
        )
        if not repository.available_dates:
            status = "no_data"
            matches = []
        else:
            matches = find_matches(repository.events, intent)
            status = "yes" if matches else "no"

    if include_proof:
        matches = rank_matches(matches)
    evidence = [_evidence_item(match) for match in matches]
    total_duration = _round_seconds(sum(match.event.duration for match in matches))
    proof = (
        _build_proof(
            evidence,
            proof_root=Path(proof_root),
            proof_ttl_hours=proof_ttl_hours,
            ffmpeg_path=ffmpeg_path,
            now=operation_now,
        )
        if include_proof
        else _proof_not_requested()
    )

    available_dates = repository.available_dates if repository else []
    missing_dates = repository.missing_dates if repository else []
    warnings = repository.warnings if repository else []
    timeline_files = repository.timeline_files if repository else []
    response = {
        "status": status,
        "answer": build_answer(status, intent, scope, matches),
        "question": intent.original_question,
        "answer_type": intent.answer_type,
        "start_date": scope.start_date.isoformat(),
        "end_date": scope.end_date.isoformat(),
        "match_count": len(matches),
        "total_duration": total_duration,
        "available_dates": [item.isoformat() for item in available_dates],
        "missing_dates": [item.isoformat() for item in missing_dates],
        "timeline_files": [str(path) for path in timeline_files],
        "warnings": warnings,
        "evidence": evidence,
        "proof": proof,
    }
    _make_response_paths_relative(response)

    if persist_response:
        store_query_response(
            response,
            include_proof=include_proof,
            response_root=response_root,
            now=operation_now,
            response_id=proof.get("query_id"),
        )
    return response
