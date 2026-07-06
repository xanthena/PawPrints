"""Reverse normalization from conversational queries to timeline evidence.

Event building turns varied model output into canonical fields. Querying needs
the reverse operation: one natural-language intent may be supported by several
canonical activities and by clues spread across activity, summary, objects,
and interaction fields.
"""

import re


QUERY_ACTIVITY_ALIASES = {
    "eating": (
        "eat", "eating", "ate", "feed", "feeding", "fed", "munch", "munching",
        "nibble", "nibbling", "having food", "had food", "meal",
    ),
    "drinking": (
        "drink", "drinking", "drank", "having water", "had water", "lapping",
    ),
    "playing": (
        "play", "playing", "played", "playing around", "played around", "playtime",
        "toy around", "toying around", "toying", "zoomies", "romping", "frolicking",
    ),
    "running": (
        "run", "running", "ran", "ran around", "running around", "sprint",
        "sprinting", "sprinted", "dash", "dashing", "dashed",
    ),
    "jumping": (
        "jump", "jumping", "jumped", "leap", "leaped", "leaping", "pounce",
        "pounced", "pouncing", "hop", "hopped", "hopping",
    ),
    "sleeping": (
        "sleep", "sleeping", "slept", "nap", "napping", "napped", "rest",
        "resting", "rested", "dozing", "dozed off",
    ),
    "scratching": (
        "scratch", "scratching", "scratched", "clawing", "clawed",
    ),
    "grooming": (
        "groom", "grooming", "groomed", "cleaning itself", "licking itself",
        "washed itself",
    ),
    "walking": (
        "walk", "walking", "walked", "stroll", "strolling", "strolled",
        "wandering", "wandered",
    ),
    "approaching": (
        "approach", "approaching", "approached", "come near", "came near",
        "go near", "went near", "move near", "moved near", "get close",
        "got close", "walk up to", "walked up to",
    ),
    "looking_out": (
        "look outside", "looking outside", "looked outside", "look out",
        "looking out", "looked out", "watch outside", "watching outside",
        "watched outside", "stare outside", "staring outside",
    ),
}


QUERY_OBJECT_ALIASES = {
    "sofa": ("sofa", "couch", "settee"),
    "bowl": ("bowl", "food bowl", "water bowl", "dish"),
    "camera": ("camera", "cctv", "security camera"),
    "window": ("window", "windowsill", "window ledge"),
    "toy": ("toy", "ball", "wand", "rope", "mouse toy"),
    "box": ("box", "cardboard box", "carton"),
    "chair": ("chair", "stool"),
    "bed": ("bed", "blanket", "bedding"),
    "door": ("door", "doorway"),
    "person": ("person", "human", "owner", "someone"),
}


# Field-specific evidence terms. A term in activity or summary is stronger
# than a contextual object/interaction clue. This allows semantic expansion
# without treating every nearby toy or bowl as proof of an action.
EVIDENCE_ACTIVITY_TERMS = {
    "eating": {
        "activity": ("eating", "feeding", "munching", "nibbling"),
        "summary": ("is eating", "was eating", "ate", "started eating", "munching", "nibbling", "having food"),
        "interaction": ("food", "food bowl", "bowl"),
        "objects": ("food", "pet food", "food bowl"),
    },
    "drinking": {
        "activity": ("drinking", "lapping"),
        "summary": ("is drinking", "was drinking", "drank", "started drinking", "lapping", "having water"),
        "interaction": ("water", "water bowl", "bowl", "cup"),
        "objects": ("water", "liquid", "water bowl"),
    },
    "playing": {
        "activity": ("playing", "pawing", "chasing", "romping", "frolicking", "zoomies"),
        "summary": (
            "playing", "played", "playful", "pawing", "batting", "swatting",
            "chasing", "toying", "toying around", "zoomies", "running around",
            "romping", "frolicking",
        ),
        "interaction": ("toy", "ball", "wand", "rope toy", "mouse toy", "playing"),
        "objects": ("toy", "ball", "wand", "rope toy", "mouse toy"),
    },
    "running": {
        "activity": ("running", "sprinting", "dashing", "zoomies"),
        "summary": ("running", "ran", "sprinting", "sprinted", "dashing", "dashed", "zoomies"),
        "interaction": (),
        "objects": (),
    },
    "jumping": {
        "activity": ("jumping", "leaping", "pouncing", "hopping"),
        "summary": ("jumping", "jumped", "leaping", "leaped", "pouncing", "pounced", "hopping", "hopped"),
        "interaction": (),
        "objects": (),
    },
    "sleeping": {
        "activity": ("sleeping", "resting", "napping", "dozing", "lying down"),
        "summary": ("sleeping", "slept", "resting", "napping", "dozing", "curled up asleep"),
        "interaction": ("resting",),
        "objects": ("bed", "blanket", "bedding"),
    },
    "scratching": {
        "activity": ("scratching", "clawing"),
        "summary": ("scratching", "scratched", "clawing", "clawed"),
        "interaction": ("scratching",),
        "objects": ("scratcher", "scratching post"),
    },
    "grooming": {
        "activity": ("grooming", "cleaning", "licking"),
        "summary": ("grooming", "cleaning itself", "licking itself", "washed itself"),
        "interaction": (),
        "objects": (),
    },
    "walking": {
        "activity": ("walking", "strolling", "wandering"),
        "summary": ("walking", "walked", "strolling", "strolled", "wandering", "wandered"),
        "interaction": (),
        "objects": (),
    },
    "approaching": {
        "activity": ("approaching", "walking", "moving closer"),
        "summary": (
            "approaching", "approached", "came near", "walked near", "moved near",
            "close to", "next to", "beside", "toward", "walked up to",
        ),
        "interaction": ("approaching", "near", "proximity"),
        "objects": (),
    },
    "looking_out": {
        "activity": ("looking out", "observing outside", "watching outside"),
        "summary": ("looking out", "looked out", "watching outside", "observing outside", "staring outside"),
        "interaction": ("window", "outside", "view"),
        "objects": ("window", "outside", "balcony"),
    },
}


NEAR_PHRASES = (
    "near", "close to", "next to", "beside", "by", "toward", "come near",
    "came near", "approach", "approached", "approaching", "walked up to",
)

FIELD_WEIGHTS = {
    "activity": 0.70,
    "summary": 0.65,
    "interaction": 0.35,
    "objects": 0.25,
}

MIN_ACTIVITY_MATCH_SCORE = 0.60


def normalize_text(value):
    text = re.sub(r"[^a-z0-9]+", " ", str(value or "").lower())
    return " ".join(text.split())


def contains_phrase(text, phrase):
    normalized_phrase = normalize_text(phrase)
    return re.search(rf"\b{re.escape(normalized_phrase)}\b", text) is not None


def find_canonical_terms(text, aliases):
    normalized = normalize_text(text)
    return tuple(
        canonical
        for canonical, phrases in aliases.items()
        if any(contains_phrase(normalized, phrase) for phrase in phrases)
    )


def matching_terms(text, terms):
    normalized = normalize_text(text)
    return tuple(term for term in terms if contains_phrase(normalized, term))
