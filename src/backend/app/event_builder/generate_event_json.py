def _object_names(objects):
    names = []

    for item in objects:
        name = item.get("name", "")
        if name and name not in names:
            names.append(name)

    return names


def generate_event_json(
    events,
    clip_start_padding_seconds=1,
    clip_end_padding_seconds=2,
):
    """Create the final JSON-ready event list."""
    final_events = []

    for index, event in enumerate(events, start=1):
        start_time = float(event.get("start_time", 0.0))
        end_time = float(event.get("end_time", start_time))
        duration = max(0.0, end_time - start_time)

        final_events.append({
            "event_id": index,
            "activities": list(event.get("activities", ["unknown"])),
            "name_of_pet": list(event.get("name_of_pet", [])),
            "start_time": start_time,
            "end_time": end_time,
            "duration": duration,
            "importance": event.get("importance_score", 0),
            "thumbnail_frame": event.get("thumbnail_frame", ""),
            "objects": _object_names(event.get("objects", [])),
            "interaction": event.get("interaction", ""),
            "summary": event.get("summary", ""),
            "clip_start": max(0.0, start_time - clip_start_padding_seconds),
            "clip_end": end_time + clip_end_padding_seconds,
        })

    return final_events
