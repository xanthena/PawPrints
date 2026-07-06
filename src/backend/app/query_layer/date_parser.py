"""Resolve basic natural-language date scopes for timeline queries."""

import re
from datetime import date, datetime, timedelta

from .models import DateScope


ISO_DATE_PATTERN = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
LAST_DAYS_PATTERN = re.compile(r"\b(?:last|past)\s+(\d+)\s+days?\b", re.IGNORECASE)


def _coerce_date(value, field_name):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError) as error:
        raise ValueError(f"{field_name} must use YYYY-MM-DD format.") from error


def parse_date_scope(question, start_date=None, end_date=None, today=None):
    """Parse explicit arguments or simple date phrases from a question."""
    current_date = _coerce_date(today, "today") if today is not None else datetime.now().astimezone().date()

    if start_date is not None or end_date is not None:
        start = _coerce_date(
            start_date if start_date is not None else end_date,
            "start_date",
        )
        end = _coerce_date(
            end_date if end_date is not None else start_date,
            "end_date",
        )
    else:
        text = str(question or "")
        explicit_dates = [date.fromisoformat(item) for item in ISO_DATE_PATTERN.findall(text)]
        if len(explicit_dates) >= 2:
            start, end = explicit_dates[0], explicit_dates[1]
        elif len(explicit_dates) == 1:
            start = end = explicit_dates[0]
        else:
            last_days = LAST_DAYS_PATTERN.search(text)
            if last_days:
                days = int(last_days.group(1))
                if days < 1:
                    raise ValueError("The requested number of days must be at least 1.")
                start = current_date - timedelta(days=days - 1)
                end = current_date
            elif re.search(r"\byesterday\b", text, re.IGNORECASE):
                start = end = current_date - timedelta(days=1)
            else:
                start = end = current_date

    if start > end:
        raise ValueError("start_date cannot be after end_date.")
    return DateScope(start_date=start, end_date=end)


def iter_dates(scope):
    """Yield every date in an inclusive DateScope."""
    current = scope.start_date
    while current <= scope.end_date:
        yield current
        current += timedelta(days=1)

