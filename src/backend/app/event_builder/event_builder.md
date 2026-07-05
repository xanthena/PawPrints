# Event Tracker Guide

The event tracker turns frame-by-frame model output into a shorter event timeline.

## `main_event_tracker.py`

Starts the pipeline. It has an `INPUT_MODE` option for choosing input data: `local` reads `src/data/jsons/qwen.json` and writes `src/data/jsons/final_timeline_qwen.json`, while `cloud` reads `src/data/jsons/gemini.json` and writes `src/data/jsons/final_timeline_gemini.json`.

It can be run either as `python -m app.event_builder.main_event_tracker` from `src/backend` or directly as `python src/backend/app/event_builder/main_event_tracker.py` from the repository root.

## `event_pipeline.py`

Connects all processing steps in order. This is the best file to read when you want to understand the full flow.

## `clean_results.py`

Fixes raw model responses. If a frame contains JSON inside a `raw_output` text block, this file extracts and parses it. If parsing fails, the frame is marked invalid.

## `normalize_results.py`

Makes similar words consistent. For example, `Looking Out`, `Peering`, and `watching outside` become `looking_out`. It also simplifies common interactions like toy and bowl.

## `detect_state_changes.py`

Turns cleaned frames into event candidates. Each valid pet frame becomes a simple candidate with activity, time, summary, objects, and whether the activity changed from the previous frame.

## `merge_consecutive_events.py`

Combines neighboring frames with the same activity into one longer event. This turns repeated frames like drinking, drinking, drinking into one drinking event with start and end times.

## `score_events.py`

Adds an importance score. More interesting actions like playing and jumping score higher than quiet actions like sleeping. Interactions, multiple cats, and high confidence add small bonuses.

## `merge_nearby_events.py`

Combines similar events that happen close together. This helps keep one activity session together when there is only a short gap between matching activities.

## `generate_event_json.py`

Builds the final output format. It adds event IDs, duration, thumbnail frame, object names, summary, and clip start/end times.

