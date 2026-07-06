"""Weighted evidence matching across every useful timeline JSON field."""

from .models import QueryMatch
from .query_normalization import (
    EVIDENCE_ACTIVITY_TERMS,
    FIELD_WEIGHTS,
    MIN_ACTIVITY_MATCH_SCORE,
    NEAR_PHRASES,
    QUERY_OBJECT_ALIASES,
    contains_phrase,
    matching_terms,
    normalize_text,
)


def _object_text(objects):
    if not isinstance(objects, list):
        return ""
    values = []
    for item in objects:
        if isinstance(item, dict):
            values.append(str(item.get("name", "")))
        else:
            values.append(str(item))
    return normalize_text(" ".join(values))


def event_fields(event):
    """Return normalized fields independently so evidence remains explainable."""
    return {
        "activity": normalize_text(event.data.get("activity", "")),
        "summary": normalize_text(event.data.get("summary", "")),
        "interaction": normalize_text(event.data.get("interaction", "")),
        "objects": _object_text(event.data.get("objects", [])),
    }


def _relation_found(fields):
    return any(
        contains_phrase(text, phrase)
        for text in fields.values()
        for phrase in NEAR_PHRASES
    )


def _activity_evidence(fields, target):
    expansion = EVIDENCE_ACTIVITY_TERMS[target]
    field_matches = {}
    score = 0.0
    relation_found = _relation_found(fields)

    for field_name, terms in expansion.items():
        matches = list(matching_terms(fields[field_name], terms))
        if target == "approaching" and field_name == "activity" and not relation_found:
            matches = [term for term in matches if term != "walking"]
        if matches:
            field_matches[field_name] = tuple(matches)
            score += FIELD_WEIGHTS[field_name]
    return score, field_matches


def _object_evidence(fields, target):
    matches = {}
    for field_name, text in fields.items():
        terms = matching_terms(text, QUERY_OBJECT_ALIASES[target])
        if terms:
            matches[field_name] = terms
    return matches


def match_event(event, intent):
    """Match activity/object intent using weighted, field-specific evidence."""
    fields = event_fields(event)
    reasons = []
    score = 0.0

    if intent.activities:
        activity_candidates = []
        for target in intent.activities:
            target_score, target_fields = _activity_evidence(fields, target)
            if target_score >= MIN_ACTIVITY_MATCH_SCORE:
                activity_candidates.append((target_score, target, target_fields))
        if not activity_candidates:
            return None

        activity_score, matched_activity, matched_fields = max(activity_candidates)
        score += activity_score
        for field_name, terms in matched_fields.items():
            reasons.append(
                f"activity.{matched_activity}.{field_name}:{'|'.join(terms)}"
            )

    if intent.objects:
        for target in intent.objects:
            field_matches = _object_evidence(fields, target)
            if not field_matches:
                return None
            score += 0.25
            for field_name, terms in field_matches.items():
                reasons.append(f"object.{target}.{field_name}:{'|'.join(terms)}")

    if intent.relation == "near":
        relation_fields = [
            field_name
            for field_name, text in fields.items()
            if any(contains_phrase(text, phrase) for phrase in NEAR_PHRASES)
        ]
        if not relation_fields:
            return None
        score += 0.15
        reasons.extend(f"relation.near.{field_name}" for field_name in relation_fields)

    if not intent.activities and not intent.objects:
        return None
    return QueryMatch(event=event, score=round(score, 3), reasons=tuple(reasons))


def find_matches(events, intent):
    """Find deterministic matches and return them in timeline order."""
    matches = []
    for event in events:
        match = match_event(event, intent)
        if match is not None:
            matches.append(match)
    return sorted(
        matches,
        key=lambda item: (
            item.event.event_date,
            item.event.source_json.name,
            item.event.start_time,
            item.event.data.get("event_id", 0),
        ),
    )
