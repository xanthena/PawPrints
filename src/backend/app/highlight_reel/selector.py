import json
import math
import re
from dataclasses import dataclass
from pathlib import Path

from .captions import caption_for_event, event_activities, event_pet_names


GENERIC_OBJECTS = {
    "animal",
    "cat",
    "floor",
    "furniture",
    "pet",
    "room",
}


def _number(value, field_name):
    try:
        number = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"Event field '{field_name}' must be a number.") from error

    if not math.isfinite(number):
        raise ValueError(f"Event field '{field_name}' must be finite.")
    return number


def _text(value):
    normalized = re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().lower())
    return normalized.strip("_")


def _objects(event):
    objects = event.get("objects", [])
    if not isinstance(objects, list):
        return set()
    return {
        normalized
        for item in objects
        if (normalized := _text(item)) and normalized not in GENERIC_OBJECTS
    }


def _interaction_group(event):
    interaction = _text(event.get("interaction"))
    activity = "_".join(_text(item) for item in event_activities(event))
    combined = f"{activity}_{interaction}"
    groups = (
        ("camera", ("camera",)),
        ("toy", ("toy", "ball", "playing")),
        ("food", ("bowl", "cup", "food", "eating", "drinking")),
        ("window", ("window", "outside", "view")),
        ("person", ("person", "human", "leg", "foot")),
        ("other_pet", ("other_cat", "proximity", "mutual")),
    )
    for group, keywords in groups:
        if any(keyword in combined for keyword in keywords):
            return group
    return interaction


def _activity_group(event):
    activity = "_".join(_text(item) for item in event_activities(event)) or "unknown"
    object_values = event.get("objects", [])
    if not isinstance(object_values, list):
        object_values = []
    context = "_".join(
        (
            activity,
            _text(event.get("interaction")),
            "_".join(_text(item) for item in object_values if item),
        )
    )

    if "camera" in context:
        return "camera_interaction"
    if any(word in activity for word in ("looking", "watching", "observing")):
        if any(word in context for word in ("window", "outside", "view")):
            return "looking_out"

    aliases = (
        ("playing", ("play", "pawing")),
        ("eating", ("eat", "feeding")),
        ("drinking", ("drink",)),
        ("sleeping", ("sleep", "rest")),
        ("grooming", ("groom",)),
        ("scratching", ("scratch",)),
        ("walking", ("walk", "approach")),
        ("running", ("run",)),
        ("jumping", ("jump", "leap")),
    )
    for group, keywords in aliases:
        if any(keyword in activity for keyword in keywords):
            return group
    return activity


def _event_segment(event, max_clip_duration):
    core_start = max(0.0, _number(event.get("start_time", 0), "start_time"))
    core_end = max(core_start, _number(event.get("end_time", core_start), "end_time"))
    available_start = max(
        0.0,
        _number(event.get("clip_start", core_start), "clip_start"),
    )
    available_end = _number(event.get("clip_end", core_end), "clip_end")

    available_start = min(available_start, core_start)
    available_end = max(available_end, core_end)
    if available_end <= available_start:
        available_end = available_start + min(max_clip_duration, 1.0)

    if available_end - available_start <= max_clip_duration:
        return available_start, available_end

    core_duration = core_end - core_start
    if core_duration >= max_clip_duration:
        start = core_start
        end = start + max_clip_duration
    else:
        padding = (max_clip_duration - core_duration) / 2
        start = core_start - padding
        end = core_end + padding

    if start < available_start:
        end += available_start - start
        start = available_start
    if end > available_end:
        start -= end - available_end
        end = available_end

    start = max(available_start, start)
    return start, min(available_end, start + max_clip_duration)


@dataclass(frozen=True)
class HighlightClip:
    event: dict
    clip_start: float
    clip_end: float
    selection_score: float
    selection_reasons: tuple[str, ...]

    @property
    def duration(self):
        return self.clip_end - self.clip_start

    @property
    def caption(self):
        return caption_for_event(self.event)

    def to_dict(self):
        return {
            "event_id": self.event.get("event_id"),
            "activities": event_activities(self.event),
            "name_of_pet": event_pet_names(self.event),
            "importance": self.event.get("importance", 0),
            "event_start": self.event.get("start_time", 0),
            "event_end": self.event.get("end_time", 0),
            "clip_start": round(self.clip_start, 3),
            "clip_end": round(self.clip_end, 3),
            "clip_duration": round(self.duration, 3),
            "objects": self.event.get("objects", []),
            "interaction": self.event.get("interaction", ""),
            "summary": self.event.get("summary", ""),
            "selection_score": round(self.selection_score, 4),
            "caption": self.caption,
            "selection_reasons": list(self.selection_reasons),
        }


@dataclass(frozen=True)
class _Candidate:
    event: dict
    index: int
    importance: float
    quality: float
    activity: str
    interaction: str
    objects: frozenset[str]
    core_start: float
    core_end: float
    clip_start: float
    clip_end: float

    @property
    def center(self):
        return (self.core_start + self.core_end) / 2


def load_timeline(timeline_path):
    """Load and validate a final Gemini/Qwen event timeline."""
    path = Path(timeline_path)
    if not path.is_file():
        raise FileNotFoundError(f"Timeline JSON does not exist: {path}")

    with path.open("r", encoding="utf-8") as file:
        events = json.load(file)

    if not isinstance(events, list):
        raise ValueError("Timeline JSON must contain a list of events.")
    for index, event in enumerate(events, start=1):
        if not isinstance(event, dict):
            raise ValueError(f"Timeline event {index} must be a JSON object.")
        for field in ("start_time", "end_time", "importance"):
            _number(event.get(field, 0), field)
    return events


def _overlap_ratio(first, second):
    overlap = max(
        0.0,
        min(first.clip_end, second.clip_end)
        - max(first.clip_start, second.clip_start),
    )
    shortest = min(
        first.clip_end - first.clip_start,
        second.clip_end - second.clip_start,
    )
    return overlap / shortest if shortest > 0 else 0.0


def _jaccard(first, second):
    union = first | second
    return len(first & second) / len(union) if union else 0.0


def _build_candidates(events, max_clip_duration):
    scores = [_number(event.get("importance", 0), "importance") for event in events]
    max_score = max(max(scores), 1.0)
    unique_scores = sorted(set(scores), reverse=True)
    rank_denominator = max(len(unique_scores) - 1, 1)
    timeline_start = min(_number(event.get("start_time", 0), "start_time") for event in events)
    timeline_end = max(_number(event.get("end_time", 0), "end_time") for event in events)

    candidates = []
    for index, (event, importance) in enumerate(zip(events, scores)):
        rank_quality = 1 - (unique_scores.index(importance) / rank_denominator)
        value_quality = max(0.0, importance) / max_score
        quality = (0.7 * value_quality) + (0.3 * rank_quality)
        clip_start, clip_end = _event_segment(event, max_clip_duration)
        core_start = _number(event.get("start_time", 0), "start_time")
        core_end = max(core_start, _number(event.get("end_time", core_start), "end_time"))
        candidates.append(
            _Candidate(
                event=event,
                index=index,
                importance=importance,
                quality=quality,
                activity=_activity_group(event),
                interaction=_interaction_group(event),
                objects=frozenset(_objects(event)),
                core_start=core_start,
                core_end=core_end,
                clip_start=clip_start,
                clip_end=clip_end,
            )
        )
    return candidates, max(timeline_end - timeline_start, 1.0)


def _candidate_score(candidate, selected, timeline_span):
    score = 0.75 * candidate.quality
    reasons = []

    if not selected:
        reasons.append(f"highest available importance ({candidate.importance:g})")
        score += min(candidate.core_end - candidate.core_start, 10.0) / 500
        return score, reasons

    selected_activities = {item.activity for item in selected}
    if candidate.activity not in selected_activities:
        score += 0.12
        reasons.append(f"adds activity diversity ({candidate.activity})")
    else:
        score -= 0.10

    selected_interactions = {item.interaction for item in selected if item.interaction}
    if candidate.interaction and candidate.interaction not in selected_interactions:
        score += 0.05
        reasons.append(f"adds interaction diversity ({candidate.interaction})")
    elif candidate.interaction:
        score -= 0.04

    max_object_similarity = max(
        (_jaccard(candidate.objects, item.objects) for item in selected),
        default=0.0,
    )
    if candidate.objects and max_object_similarity == 0:
        score += 0.03
        reasons.append("adds different objects")
    else:
        score -= 0.04 * max_object_similarity

    min_distance = min(abs(candidate.center - item.center) for item in selected)
    temporal_novelty = min(1.0, (min_distance * len(selected)) / timeline_span)
    score += 0.05 * temporal_novelty
    if temporal_novelty >= 0.35:
        reasons.append("covers a different part of the timeline")

    max_overlap = max(_overlap_ratio(candidate, item) for item in selected)
    score -= 0.30 * max_overlap
    score += min(candidate.core_end - candidate.core_start, 10.0) / 500

    if not reasons:
        reasons.append("next strongest non-duplicate event")
    return score, reasons


def select_highlights(events, max_clips=5, max_clip_duration=10.0):
    """Select a short, diverse set relative to the day's available scores.

    There is intentionally no absolute importance threshold. The greedy ranking
    combines within-timeline importance with activity, interaction, object,
    temporal, and overlap diversity.
    """
    if max_clips < 1:
        raise ValueError("max_clips must be at least 1.")
    if max_clip_duration <= 0:
        raise ValueError("max_clip_duration must be greater than 0.")
    if not events:
        return []

    candidates, timeline_span = _build_candidates(events, max_clip_duration)
    selected = []
    scored_selections = []

    while candidates and len(selected) < max_clips:
        scored = []
        for candidate in candidates:
            score, reasons = _candidate_score(candidate, selected, timeline_span)
            scored.append((score, candidate.importance, -candidate.index, candidate, reasons))

        score, _, _, chosen, reasons = max(scored, key=lambda item: item[:3])
        selected.append(chosen)
        scored_selections.append(
            HighlightClip(
                event=chosen.event,
                clip_start=chosen.clip_start,
                clip_end=chosen.clip_end,
                selection_score=score,
                selection_reasons=tuple(reasons),
            )
        )
        candidates.remove(chosen)

    return sorted(scored_selections, key=lambda clip: clip.clip_start)
