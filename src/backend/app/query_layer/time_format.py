"""Formatting helpers for timestamps relative to a source video."""

import math


def format_video_timestamp(seconds):
    """Format seconds as HH:MM:SS.mmm without wrapping after 24 hours."""
    value = float(seconds)
    if not math.isfinite(value) or value < 0:
        raise ValueError("Video timestamp must be a finite, non-negative number.")

    total_milliseconds = round(value * 1000)
    hours, remainder = divmod(total_milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    whole_seconds, milliseconds = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{whole_seconds:02d}.{milliseconds:03d}"

