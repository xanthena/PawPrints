"""Public APIs for selecting and rendering highlight reels."""

from .pipeline import generate_highlight_reel
from .selector import load_timeline, select_highlights

__all__ = ["generate_highlight_reel", "load_timeline", "select_highlights"]
