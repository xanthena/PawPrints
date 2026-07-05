from event_tracker.merge_consecutive_events import _merge_event_data


def merge_nearby_events(events, threshold_seconds=20):
    """Merge same-activity events separated by a short gap."""
    if not events:
        return []

    merged = []
    current = events[0].copy()

    for incoming in events[1:]:
        gap = incoming["start_time"] - current["end_time"]
        if incoming["activity"] == current["activity"] and gap < threshold_seconds:
            _merge_event_data(current, incoming)
            current["importance_score"] = max(
                current.get("importance_score", 0),
                incoming.get("importance_score", 0),
            )
            continue

        merged.append(current)
        current = incoming.copy()

    merged.append(current)
    return merged
