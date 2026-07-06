def _unique_objects(objects):
    seen = set()
    unique = []

    for item in objects:
        name = item.get("name", "")
        if not name or name in seen:
            continue
        seen.add(name)
        unique.append(item)

    return unique


def _unique_values(values):
    seen = set()
    unique = []
    for value in values:
        text = str(value or "").strip()
        key = text.casefold()
        if text and key not in seen:
            seen.add(key)
            unique.append(text)
    return unique


def _same_activities(first, second):
    return set(first.get("activities", [])) == set(second.get("activities", []))


def _merge_event_data(current, incoming):
    current["end_time"] = incoming["end_time"]
    current["frames"].extend(incoming["frames"])
    current["activities"] = _unique_values(
        current.get("activities", []) + incoming.get("activities", [])
    )
    current["name_of_pet"] = _unique_values(
        current.get("name_of_pet", []) + incoming.get("name_of_pet", [])
    )
    current["objects"] = _unique_objects(current["objects"] + incoming["objects"])

    if incoming["interaction"] and not current["interaction"]:
        current["interaction"] = incoming["interaction"]

    if incoming["summary"] and incoming["confidence"] >= current["confidence"]:
        current["summary"] = incoming["summary"]
        current["thumbnail_frame"] = incoming["thumbnail_frame"]

    current["confidence"] = max(current["confidence"], incoming["confidence"])
    current["duration"] = current["end_time"] - current["start_time"]


def merge_consecutive_events(events):
    """Merge neighboring candidates that have the same activity set."""
    if not events:
        return []

    merged = []
    current = events[0].copy()
    current["duration"] = current["end_time"] - current["start_time"]

    for incoming in events[1:]:
        if _same_activities(incoming, current):
            _merge_event_data(current, incoming)
            continue

        merged.append(current)
        current = incoming.copy()
        current["duration"] = current["end_time"] - current["start_time"]

    merged.append(current)
    return merged
