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
        # frames from a motion detector with real burst timing (see
        # run_on_candidates.py) can supply an actual end_time; frames with
        # no such signal fall back to the original instantaneous behavior.
        end_time = float(frame.get("end_time", timestamp))

        candidates.append({
            "activity": activity,
            "start_time": timestamp,
            "end_time": end_time,
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
