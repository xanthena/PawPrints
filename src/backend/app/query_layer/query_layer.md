# Query layer

The query layer answers basic questions using dated final timeline JSON files.
It does not call an external language model. Dates, activities, objects, and
relationships are parsed deterministically and every positive answer includes
the matching timeline evidence.

## Supported date scopes

- No date or `today`: current local date
- `yesterday`
- An exact ISO date such as `2026-07-06`
- An inclusive range such as `2026-07-01 to 2026-07-06`
- `last N days` or `past N days`
- Explicit `start_date` and `end_date` API/CLI arguments

For every date, the repository loads all distinct videos from:

```text
src/data/jsons/final_timeline/YYYY-MM-DD/*.json
```

If the same video was processed repeatedly, only its newest numeric version is
queried so events are not counted twice.

## Supported question types

Initial activity vocabulary includes eating, drinking, running, jumping,
playing, sleeping, scratching, grooming, walking, approaching, and looking
outside. Object aliases include sofa/couch, bowl, camera, window, toy, box,
chair, bed, door, and person.

Examples:

```text
Did my cat eat today?
Was my cat running around yesterday?
Did my cat jump from 2026-07-01 to 2026-07-06?
Did my cat come near the sofa?
How long did my cat play today?
How many times did my cat drink in the last 3 days?
```

## Evidence response

Every match contains:

- Full source timeline JSON filename and path
- Full original video filename and path
- Event start/end in seconds and `HH:MM:SS.mmm`
- Event duration
- Proof clip start/end and duration
- Grouped activities, pet names, context, relevance score, and match reasons
- Proof segment number when a proof video was requested

`no` means timeline data exists but no event matched. `no_data` means there was
no usable timeline for the requested date range. Missing footage never becomes
a false negative.

## Optional proof video

Set `include_proof=True` or pass `--proof`. Matching clip ranges are ordered by
descending weighted relevance with stable chronological tie-breakers.
Overlapping ranges from the same video are merged without losing that order;
remaining ranges—even from different videos or days—are normalized and
stitched into one video-only MP4.

Temporary proofs are stored under:

```text
src/results/query-proofs/temp/YYYY-MM-DD/<query-id>_query_proof.mp4
```

They use unique IDs and expire after 24 hours by default. Expired managed proof
files are cleaned before creating a new proof. A proof rendering failure is
reported in the `proof` object and does not remove the textual answer.

## Python API

```python
from app.query_layer import answer_query

response = answer_query(
    "Did my cat eat today?",
    include_proof=True,
)
```

## CLI

From `src/backend`:

```powershell
python -m app.query_layer "Did my cat eat today?"
python -m app.query_layer "Did my cat jump in the last 3 days?" --proof
python -m app.query_layer "Did my cat eat?" --start-date 2026-07-01 --end-date 2026-07-06
```

Install `app/highlight_reel/requirements.txt` if FFmpeg is not already on PATH.

## Current limitations

- Event timestamps are offsets within the source video, not wall-clock times.
- Identity quality depends on registered reference photos and the model match.
- Spatial questions depend on the model recording the relationship in the
  activity, objects, interaction, or summary fields.
