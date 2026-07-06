ACTIVITY_MAP = {
    "alert": "watching",
    "approaching": "walking",
    "bending": "playing",
    "climbing": "climbing",
    "crouching": "sitting",
    "curled up": "sleeping",
    "drank": "drinking",
    "drink": "drinking",
    "looking": "looking_out",
    "looking out": "looking_out",
    "looking_out": "looking_out",
    "looking outside": "looking_out",
    "looking through window": "looking_out",
    "looking under furniture": "looking_under",
    "observing": "watching",
    "pawing": "playing",
    "peering": "looking_out",
    "peeking": "looking_out",
    "play": "playing",
    "playing": "playing",
    "playing with toy": "playing",
    "ran": "running",
    "running": "running",
    "rest": "sleeping",
    "lying": "sleeping",
    "lying down": "sleeping",
    "resting": "sleeping",
    "scratched": "scratching",
    "scratch": "scratching",
    "scratching": "scratching",
    "seated": "sitting",
    "sitting": "sitting",
    "sleep": "sleeping",
    "sleeping": "sleeping",
    "standing": "standing",
    "staring": "watching",
    "staring outside": "looking_out",
    "watching": "watching",
    "watching outside": "looking_out",
    "watching out": "looking_out",
    "walk": "walking",
    "walked": "walking",
    "walking": "walking",
    "jumping": "jumping",
    "jumped": "jumping",
    "leaping": "jumping",
    "drinking": "drinking",
    "eating from bowl": "eating",
    "eating": "eating",
    "feeding": "eating",
}

INTERACTION_MAP = {
    "bowl": "bowl",
    "cat toy": "toy",
    "eating from a pink bowl": "bowl",
    "food": "food",
    "food bowl": "bowl",
    "in a pink bowl": "bowl",
    "in a pink cup": "cup",
    "kitten approaching the cat toy": "toy",
    "kitten interacting with toy": "toy",
    "looking at each other": "other_cat",
    "looking out window": "window",
    "looking under furniture": "furniture",
    "person": "person",
    "person's leg": "person",
    "pink bowl": "bowl",
    "pink cup": "cup",
    "playing with cat toy": "toy",
    "playing with piano": "piano",
    "playing with toy": "toy",
    "playing with toys": "toy",
    "rope toy": "toy",
    "the cat is interacting with the toy": "toy",
    "the cat is interacting with the toy by pawing at it.": "toy",
    "toy": "toy",
    "toys": "toy",
    "under furniture": "furniture",
    "underneath person's leg": "person",
    "water bowl": "bowl",
    "window": "window",
}

OBJECT_MAP = {
    "animal": "animal",
    "ball": "ball",
    "black and white cat": "cat",
    "black cat": "cat",
    "box": "box",
    "cat": "cat",
    "cat head": "cat",
    "cat paw": "cat",
    "cat playing with a colorful toy": "toy",
    "cat toy": "toy",
    "cat toy with a ball and rope": "toy",
    "cat toy with ball and rope": "toy",
    "cat toy with colorful rope and ball": "toy",
    "cat's head": "cat",
    "colorful toy": "toy",
    "cup": "cup",
    "dog": "dog",
    "food": "food",
    "furniture": "furniture",
    "kitten": "cat",
    "kitty": "cat",
    "newspaper": "newspaper",
    "newspaper on floor": "newspaper",
    "orange cat": "cat",
    "orange tabby cat": "cat",
    "person": "person",
    "piano": "piano",
    "pink bowl": "bowl",
    "pink cup": "cup",
    "rope toy": "toy",
    "striped cat": "cat",
    "tennis ball": "ball",
    "toothbrush toy": "toy",
    "toy": "toy",
    "toy ball": "ball",
    "water bowl": "bowl",
    "white and black cat": "cat",
    "white cat": "cat",
}

INTERACTION_PHRASES = (
    ("toy", "toy"),
    ("ball", "ball"),
    ("bowl", "bowl"),
    ("cup", "cup"),
    ("window", "window"),
    ("furniture", "furniture"),
    ("under", "furniture"),
    ("leg", "person"),
    ("person", "person"),
    ("piano", "piano"),
    ("each other", "other_cat"),
)

OBJECT_PHRASES = (
    ("cat", "cat"),
    ("kitten", "cat"),
    ("toy", "toy"),
    ("ball", "ball"),
    ("bowl", "bowl"),
    ("cup", "cup"),
    ("newspaper", "newspaper"),
    ("piano", "piano"),
    ("dog", "dog"),
    ("person", "person"),
    ("furniture", "furniture"),
)


def _normalize_text(value):
    text = str(value or "").strip().lower().replace("-", " ").replace("_", " ")
    return " ".join(text.strip(" .,:;!?\"'()[]{}").split())


def _normalize_activity(activity):
    normalized = _normalize_text(activity)
    return ACTIVITY_MAP.get(normalized, normalized.replace(" ", "_") or "unknown")


def _normalize_activities(activities):
    if not isinstance(activities, list):
        activities = [activities]
    normalized = []
    for activity in activities:
        canonical = _normalize_activity(activity)
        if canonical not in normalized:
            normalized.append(canonical)
    return normalized or ["unknown"]


def _normalize_interaction(interaction):
    normalized = _normalize_text(interaction)
    if not normalized:
        return ""
    if normalized in INTERACTION_MAP:
        return INTERACTION_MAP[normalized]
    for phrase, replacement in INTERACTION_PHRASES:
        if phrase in normalized:
            return replacement
    return normalized


def _normalize_object_name(name):
    normalized = _normalize_text(name)
    if normalized in OBJECT_MAP:
        return OBJECT_MAP[normalized]
    for phrase, replacement in OBJECT_PHRASES:
        if phrase in normalized:
            return replacement
    return normalized


def normalize_results(results):
    """Standardize activity, interaction, and object names."""
    normalized_results = []

    for frame in results:
        result = frame["result"].copy()
        result["activities"] = _normalize_activities(
            result.get("activities", result.get("activity", "unknown"))
        )
        result.pop("activity", None)
        result["interaction"] = _normalize_interaction(result.get("interaction"))
        result["objects"] = [
            {
                "name": _normalize_object_name(item.get("name", "")),
                "confidence": item.get("confidence", 0.0),
            }
            for item in result.get("objects", [])
            if _normalize_object_name(item.get("name", ""))
        ]

        normalized_frame = frame.copy()
        normalized_frame["result"] = result
        normalized_results.append(normalized_frame)

    return sorted(normalized_results, key=lambda item: item.get("timestamp", 0.0))
