import json
from pathlib import Path

from .clean_results import clean_results
from .detect_state_changes import detect_state_changes
from .generate_event_json import generate_event_json
from .merge_consecutive_events import merge_consecutive_events
from .merge_nearby_events import merge_nearby_events
from .normalize_results import normalize_results
from .score_events import score_events


def run_event_pipeline(input_file, output_file):
    """Run the raw JSON to final event timeline pipeline."""
    input_path = Path(input_file)
    output_path = Path(output_file)

    with input_path.open("r", encoding="utf-8") as file:
        raw_results = json.load(file)

    cleaned = clean_results(raw_results)
    normalized = normalize_results(cleaned)
    state_events = detect_state_changes(normalized)
    consecutive_events = merge_consecutive_events(state_events)
    scored_events = score_events(consecutive_events)
    merged_events = merge_nearby_events(scored_events)
    final_events = generate_event_json(merged_events)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(final_events, file, indent=4, ensure_ascii=False)

    return final_events

