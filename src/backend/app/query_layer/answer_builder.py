"""Human-readable answers backed by structured timeline evidence."""


def _occurrence_phrase(count):
    if count == 1:
        return "once"
    if count == 2:
        return "twice"
    return f"{count} times"


def _date_phrase(scope, question):
    lowered = question.lower()
    if scope.start_date == scope.end_date:
        if "today" in lowered:
            return "today"
        if "yesterday" in lowered:
            return "yesterday"
        return f"on {scope.start_date.isoformat()}"
    return f"from {scope.start_date.isoformat()} to {scope.end_date.isoformat()}"


def build_answer(status, intent, scope, matches):
    """Build a concise answer while keeping status semantics explicit."""
    date_phrase = _date_phrase(scope, intent.original_question)
    target = intent.target_label

    if status == "unsupported":
        return (
            "I could not identify a supported activity or object in that question. "
            "Try asking about eating, drinking, running, jumping, playing, sleeping, "
            "walking, approaching, or a visible object such as a sofa or bowl."
        )
    if status == "no_data":
        return f"No timeline data is available {date_phrase}."
    if status == "no":
        return f"I found timeline data {date_phrase}, but no {target} event was recorded."

    count = len(matches)
    total_duration = sum(match.event.duration for match in matches)
    occurrence = _occurrence_phrase(count)
    if intent.answer_type == "count":
        return f"Your cat was observed {target} {occurrence} {date_phrase}."
    if intent.answer_type == "duration":
        return (
            f"Your cat was observed {target} for about {total_duration:.1f} seconds "
            f"across {count} event{'s' if count != 1 else ''} {date_phrase}."
        )
    return (
        f"Yes. Your cat was observed {target} {occurrence} {date_phrase} "
        f"for about {total_duration:.1f} seconds."
    )

