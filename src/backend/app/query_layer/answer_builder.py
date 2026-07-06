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

def _unique_names(values):
    names = []
    seen = set()
    for value in values:
        name = str(value or "").strip()
        if name and name.casefold() not in seen:
            names.append(name)
            seen.add(name.casefold())
    return names


def _subject(intent, matches):
    names = _unique_names(intent.pet_names)
    if not names:
        names = _unique_names(
            name for match in matches for name in match.event.pet_names
        )
    if not names:
        return "Your cat", "was"
    if len(names) == 1:
        return names[0], "was"
    return f"{', '.join(names[:-1])} and {names[-1]}", "were"



def build_answer(status, intent, scope, matches):
    """Build a concise answer while keeping status semantics explicit."""
    date_phrase = _date_phrase(scope, intent.original_question)
    target = intent.target_label

    subject, subject_verb = _subject(intent, matches)
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
        return f"{subject} {subject_verb} observed {target} {occurrence} {date_phrase}."
    if intent.answer_type == "duration":
        return (
            f"{subject} {subject_verb} observed {target} for about {total_duration:.1f} seconds "
            f"across {count} event{'s' if count != 1 else ''} {date_phrase}."
        )
    return (
        f"Yes. {subject} {subject_verb} observed {target} {occurrence} {date_phrase} "
        f"for about {total_duration:.1f} seconds."
    )

