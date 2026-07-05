"""
Converts frame-level model outputs into a clean timeline.
"""

from typing import List, Dict


def normalize_activity(activity: str) -> str:
    """
    Standardize activity labels.
    """

    if not activity:
        return "unknown"

    activity = activity.lower().strip()

    mapping = {
        "looking": "looking",
        "looking out": "looking",
        "peering": "looking",
        "peeking": "looking",

        "resting": "sleeping",

        "lying": "sleeping",
        "lying down": "sleeping",

        "walking": "walking",

        "playing": "playing",

        "jumping": "jumping",

        "drinking": "drinking",

        "eating": "eating",

        "sleeping": "sleeping",

        "scratching": "scratching",

        "sitting": "sitting"
    }

    return mapping.get(activity, activity)


def build_timeline(results: List[Dict]) -> List[Dict]:
    """
    Converts benchmark JSON into a chronological timeline.
    """

    timeline = []

    for frame in results:

        result = frame.get("result", {})

        if not result.get("pet_detected", False):
            continue

        activity = normalize_activity(
            result.get("activity", "unknown")
        )

        timeline.append({

            "timestamp": frame["timestamp"],

            "frame_number": frame["frame_number"],

            "frame": frame["frame"],

            "activity": activity,

            "confidence": result.get(
                "activity_confidence",
                0.0
            ),

            "interaction": result.get(
                "interaction",
                ""
            ),

            "objects": result.get(
                "objects",
                []
            ),

            "summary": result.get(
                "summary",
                ""
            )

        })

    timeline.sort(key=lambda x: x["timestamp"])

    return timeline