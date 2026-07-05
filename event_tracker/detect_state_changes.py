def detect_state_changes(results):
    """Convert normalized frames into ordered event candidates."""
    candidates = []
    current_activity = None

    for frame in results:
        result = frame.get("result", {})
        if not result.get("pet_detected", False) or result.get("invalid"):
            continue

        activity = result.get("activity", "unknown")
        timestamp = float(frame.get("timestamp", 0.0))

        candidates.append({
            "activity": activity,
            "start_time": timestamp,
            "end_time": timestamp,
            "frames": [frame.get("frame", "")],
            "thumbnail_frame": frame.get("frame", ""),
            "objects": result.get("objects", []),
            "interaction": result.get("interaction", ""),
            "summary": result.get("summary", ""),
            "confidence": float(result.get("confidence", 0.0)),
            "state_changed": activity != current_activity,
        })

        current_activity = activity

    return candidates
