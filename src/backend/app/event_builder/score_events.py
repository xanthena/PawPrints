ACTIVITY_SCORES = {
    "playing": 10,
    "jumping": 10,
    "drinking": 4,
    "eating": 4,
    "walking": 2,
    "sleeping": 1,
    "scratching": 4,
    "looking_out": 2,
    "sitting": 1,
}


def _has_multiple_cats(objects, pet_names):
    if len(pet_names) > 1:
        return True

    cat_count = 0

    for item in objects:
        if "cat" in item.get("name", ""):
            cat_count += 1

    return cat_count > 1


def score_events(events):
    """Add an importance score to each event."""
    scored_events = []

    for event in events:
        activities = event.get("activities", ["unknown"])
        score = max(
            (ACTIVITY_SCORES.get(activity, 1) for activity in activities),
            default=1,
        )

        if event.get("interaction"):
            score += 2

        if _has_multiple_cats(
            event.get("objects", []),
            event.get("name_of_pet", []),
        ):
            score += 3

        if event.get("confidence", 0.0) > 0.95:
            score += 1

        scored_event = event.copy()
        scored_event["importance_score"] = score
        scored_events.append(scored_event)

    return scored_events
