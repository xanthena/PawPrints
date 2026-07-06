"""Rule-based intent extraction for conversational pet questions."""

from .models import QueryIntent
from .query_normalization import (
    NEAR_PHRASES,
    QUERY_ACTIVITY_ALIASES,
    QUERY_OBJECT_ALIASES,
    contains_phrase,
    find_canonical_terms,
    normalize_text,
)


def parse_query_intent(question, known_pet_names=()):
    """Extract canonical activities, objects, relations, and answer type."""
    original = str(question or "").strip()
    if not original:
        raise ValueError("question is required.")

    text = normalize_text(original)
    activities = find_canonical_terms(text, QUERY_ACTIVITY_ALIASES)
    objects = find_canonical_terms(text, QUERY_OBJECT_ALIASES)
    pet_names = tuple(
        str(name)
        for name in known_pet_names
        if contains_phrase(text, str(name))
    )
    relation = "near" if any(contains_phrase(text, phrase) for phrase in NEAR_PHRASES) else None

    if contains_phrase(text, "how long") or contains_phrase(text, "how much time"):
        answer_type = "duration"
    elif contains_phrase(text, "how many") or contains_phrase(text, "how often"):
        answer_type = "count"
    else:
        answer_type = "existence"

    return QueryIntent(
        original_question=original,
        answer_type=answer_type,
        activities=activities,
        objects=objects,
        relation=relation,
        pet_names=pet_names,
    )

