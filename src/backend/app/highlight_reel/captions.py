"""Short, name-aware descriptions for burned-in highlight subtitles."""

import re
import textwrap


MAX_CAPTION_CHARACTERS = 92


def event_activities(event):
    values = event.get("activities")
    if not isinstance(values, list):
        values = [event.get("activity", "unknown")]
    activities = []
    for value in values:
        activity = str(value or "").strip()
        if activity and activity not in activities:
            activities.append(activity)
    return activities or ["unknown"]


def event_pet_names(event):
    values = event.get("name_of_pet", [])
    if isinstance(values, str):
        values = [values]
    if not isinstance(values, list):
        return []
    names = []
    seen = set()
    for value in values:
        name = " ".join(str(value or "").strip().split())
        if name and name.casefold() not in seen:
            names.append(name)
            seen.add(name.casefold())
    return names


def _joined_names(names):
    if len(names) == 1:
        return names[0]
    return f"{', '.join(names[:-1])} and {names[-1]}"


def _personalize_summary(summary, names):
    if not names:
        return summary
    subject = _joined_names(names)
    if len(names) > 1:
        summary = re.sub(
            r"\b(?:two|both)\s+(?:cats|kittens|kitties)\b",
            subject,
            summary,
            count=1,
            flags=re.IGNORECASE,
        )
    else:
        summary = re.sub(
            r"\b(?:a|an|the)\s+(?:(?:[a-z-]+)\s+){0,3}(?:cat|kitten|kitty)\b",
            subject,
            summary,
            count=1,
            flags=re.IGNORECASE,
        )
    return summary


def caption_for_event(event, max_characters=MAX_CAPTION_CHARACTERS):
    """Return one clean subtitle sentence derived from timeline evidence."""
    names = event_pet_names(event)
    summary = " ".join(str(event.get("summary", "")).strip().split())
    if summary:
        caption = _personalize_summary(summary, names)
    else:
        activities = " and ".join(
            activity.replace("_", " ") for activity in event_activities(event)
        )
        subject = _joined_names(names) if names else "A cat"
        caption = f"{subject} — {activities}"

    caption = caption.rstrip(" .")
    if len(caption) <= max_characters:
        return caption
    return textwrap.shorten(
        caption,
        width=max_characters,
        placeholder="…",
    )
