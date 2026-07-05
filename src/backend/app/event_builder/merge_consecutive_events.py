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


def _merge_event_data(current, incoming):
    current["end_time"] = incoming["end_time"]
    current["frames"].extend(incoming["frames"])
    current["objects"] = _unique_objects(current["objects"] + incoming["objects"])

    if incoming["interaction"] and not current["interaction"]:
        current["interaction"] = incoming["interaction"]

    if incoming["summary"] and incoming["confidence"] >= current["confidence"]:
        current["summary"] = incoming["summary"]
        current["thumbnail_frame"] = incoming["thumbnail_frame"]

    current["confidence"] = max(current["confidence"], incoming["confidence"])
    current["duration"] = current["end_time"] - current["start_time"]


def merge_consecutive_events(events):
    """Merge neighboring frame candidates that have the same activity."""
    if not events:
        return []

    merged = []
    current = events[0].copy()
    current["duration"] = current["end_time"] - current["start_time"]

    for incoming in events[1:]:
        if incoming["activity"] == current["activity"]:
            _merge_event_data(current, incoming)
            continue

        merged.append(current)
        current = incoming.copy()
        current["duration"] = current["end_time"] - current["start_time"]

    merged.append(current)
    return merged
