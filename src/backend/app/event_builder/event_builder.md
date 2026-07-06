# Event Tracker Guide

The event tracker turns frame-by-frame model output into a shorter event timeline.

## `main_event_tracker.py`

Starts the pipeline for one video. It reads the overwrite-in-place vision output
at `src/data/jsons/<video_stem>_vision.json`, then writes the final timeline to:

```text
src/data/jsons/final_timeline/YYYY-MM-DD/<video_stem>_final_timeline.json
```

The date is the machine's current local date. Final timelines are never
overwritten. Different videos naturally have different filenames; running the
same video again on the same day adds `_2`, `_3`, and so on.

Run it from `src/backend`:

```powershell
python -m app.event_builder.main_event_tracker <video_stem>
```

An explicit input is also supported:

```powershell
python -m app.event_builder.main_event_tracker <video_stem> --input C:\path\to\video_vision.json
```

## `timeline_storage.py`

Owns date-folder naming, video-based output naming, collision-safe paths, and
newest-file lookup. The highlight-reel module uses the same helper so both
modules agree on where today's final timelines live.

## `event_pipeline.py`

Connects all processing steps in order. This is the best file to read when you
want to understand the full event-building flow.

## `clean_results.py`

Fixes raw model responses. If a frame contains JSON inside a `raw_output` text
block, this file extracts and parses it. If parsing fails, the frame is marked
invalid.

## `normalize_results.py`

Makes similar words consistent. For example, `Looking Out`, `Peering`, and
`watching outside` become `looking_out`. It also simplifies common interactions
like toy and bowl.

## `detect_state_changes.py`

Turns cleaned frames into event candidates. Each valid pet frame becomes a
candidate with activity and pet-name lists, time, summary, objects, and state-change information.

## `merge_consecutive_events.py`

Combines neighboring frames with the same activity set into one longer event.

## `score_events.py`

Adds an importance score. Interesting actions like playing and jumping score
higher than quiet actions like sleeping.

## `merge_nearby_events.py`

Combines similar events that happen close together.

## `generate_event_json.py`

Builds the final output format, including event IDs, duration, thumbnail frame,
object names, summary, and clip start/end times. New timelines write `activities`
and `name_of_pet` as lists, with one second before and two seconds after events.

