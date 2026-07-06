# PawPrints Codebase Guide

This file is the durable engineering map for PawPrints. It is intentionally
more detailed than the per-module README files so that a future coding session
can recover the architecture, contracts, conventions, and design intent without
having to rediscover the repository from scratch.

## 1. Product purpose

PawPrints turns pet CCTV footage into four useful artifacts:

1. a low-cost stream of candidate frames selected by local motion detection;
2. structured vision-model observations for those candidate frames;
3. a compact, dated event timeline that can be queried deterministically;
4. rendered media: evidence/proof videos for queries and a curated highlight
   reel.

There is also a Vite/React/Electron prototype. The frontend currently displays
mock footage cards and lets a user select a video, but it is not connected to
the Python backend yet.

The backend is a collection of importable Python services and command-line
entry points, not an HTTP service. Future UI integration therefore needs a
transport boundary (for example Electron IPC to a managed Python process, or a
small local HTTP API). See `integration_issues.md` for concrete integration
gaps that should not be hidden by the domain code.

## 2. Repository map

```text
PawPrints/
|-- CODEBASE_GUIDE.md           durable architecture and coding guide
|-- tasks.md                    requested work and implementation journal
|-- integration_issues.md       UI/backend integration audit (when issues exist)
|-- security_risks.md           security/privacy audit (when risks exist)
|-- src/
|   |-- backend/
|   |   |-- app/
|   |   |   |-- motion_detector/   video sampling and candidate-frame selection
|   |   |   |-- vision_model/      model routing and image inference
|   |   |   |-- event_builder/     raw observations to final timeline
|   |   |   |-- query_layer/       deterministic questions and proof videos
|   |   |   `-- highlight_reel/    selection and rendered highlight MP4
|   |   |-- tests/                  standard-library unittest suite
|   |   |-- .env.example           model configuration template
|   |   `-- requirements.txt
|   |-- data/
|   |   |-- source_video/           footage used by downstream video renderers
|   |   |-- frames/                 extracted candidate JPEGs
|   |   |-- events/<video>/         motion-stage `events.jsonl`
|   |   `-- jsons/                  raw vision and final timeline JSON
|   |-- results/                    proof, highlight, and detector artifacts
|   `-- frontend/                   React/Vite/Electron prototype
`-- documentation/                  currently empty legacy documentation folder
```

There is no database; timeline persistence is filesystem-based JSON.

## 3. End-to-end lifecycle

```text
source video / camera / RTSP URL
        |
        v
motion_detector.main_stream_worker
  - sample every 0.5 seconds
  - frame-difference detection on a 320px-wide image
  - candidate queue applies a 4-second cooldown
  - periodic still ping (default 300 seconds)
        |
        +--> src/data/frames/frame_<video>_<frame>_<seconds>s.jpg
        `--> src/data/events/<video>/events.jsonl
                |
                v
vision_model.main_run_on_candidates
  - skips burst_end markers
  - gives each candidate an end_time from the next event
  - validates image path/type/size
  - calls primary model, then optional fallback model
        |
        `--> src/data/jsons/<video>_vision.json (overwritten on rerun)
                |
                v
event_builder.main_event_tracker
  clean -> normalize -> candidates -> merge -> score -> merge -> serialize
        |
        `--> src/data/jsons/final_timeline/YYYY-MM-DD/
             <video>_final_timeline[_N].json (never overwritten)
                    |                         |
                    v                         v
             query_layer                 highlight_reel
             deterministic matching      relative score + diversity
                    |                         |
                    +--> response JSON        +--> dated reel MP4
                    `--> optional proof MP4   `--> paired manifest JSON
```

The video filename stem is the join key across the pipeline. A timeline named
`kitchen_final_timeline_2.json` maps back to `source_video/kitchen.mp4`. Numeric
suffixes denote repeated processing, not a different source video.

## 4. Motion detection in detail

### 4.1 Production-style stream worker

`app/motion_detector/main_stream_worker.py` is the main candidate-extraction
path. `stream_events()` accepts anything OpenCV `VideoCapture` can open, so the
same iterator can handle a finished file or an unbounded stream.

Important constants:

- `SAMPLE_INTERVAL_SEC = 0.5`: only sampled frames reach the detector;
- `SMALL_WIDTH = 320`: detection runs on a small aspect-preserving frame;
- `COOLDOWN_SEC = 4.0`: long movement emits at most one candidate per window;
- `STILL_PING_INTERVAL_SEC = 300.0`: prolonged stillness is periodically
  rechecked, which is important for sleeping/resting events;
- `VISION_LONG_EDGE = 768`: candidate JPEGs keep their aspect ratio and are
  resized to a roughly model-friendly pixel budget.

`CandidateFrameQueue.observe()` is a small state machine:

- still -> motion: emit a `candidate` immediately;
- continued motion: emit another candidate after the cooldown;
- motion -> still: emit one metadata-only `burst_end` marker;
- continued stillness: emit a `still_ping` candidate at the configured interval.

Every emitted dictionary has a `kind`. Candidate records also include the
trigger, frame index, timestamp, motion statistics, and initially the OpenCV
frame. `persist_event()` removes that in-memory frame, saves a resized JPEG,
adds `frame_path`, and appends one JSON line to `events.jsonl`.

The events file is opened in append mode. A caller that intentionally
reprocesses the same video must account for an existing events file; this is a
known integration concern because duplicate candidate records would otherwise
be analyzed.

### 4.2 Detector implementations

- `FrameDiffDetector`: grayscale -> Gaussian blur -> absolute difference from
  the previous frame -> binary threshold -> shared decision logic.
- `MOG2Detector`: OpenCV background subtraction -> remove shadow pixels ->
  shared decision logic.
- `MotionDetector._decide()`: either counts changed pixels or filters contours
  by an area proportional to frame size (`min_area_frac`, default 0.5%).

`main_harness.py` is a benchmarking tool, not the production stream path. It
runs full/small frame-diff and MOG2 variants and stores timing/motion summaries
under `src/results/run_<timestamp>`.

## 5. Vision inference in detail

### 5.1 Candidate timing

`app/vision_model/main_run_on_candidates.py` loads the motion JSONL for a video.
It ignores `burst_end` records as inference candidates, but those markers still
matter: `compute_end_time()` sets each candidate's end to the timestamp of the
next event of any kind. This makes adjacent candidate spans non-overlapping and
lets the last candidate in a movement burst end exactly when stillness starts.
The final candidate falls back to zero duration if the stream ended without a
following marker.

The vision result record carries frame identity, `timestamp`, `end_time`, model
provenance (`model_used`, `fell_back`), and the parsed model result. A response
that is not valid JSON is preserved in `{ "raw_output": ... }`; the event
builder owns the tolerant repair/parsing step.

The raw vision output for a video is intentionally overwritten on every run.
Historical, non-overwriting storage starts only at final-timeline generation.

### 5.2 Model router

`model_router.py` supports four names:

- `qwen`: a local Ollama model (`OLLAMA_MODEL`);
- `gemini`: Google GenAI, API-key or Vertex authentication;
- `claude`: Anthropic Messages API;
- `openai`: OpenAI vision through Chat Completions.

The explicit `primary=` and `fallback=` function parameters override
`VISION_MODEL_PRIMARY` and `VISION_MODEL_FALLBACK`. The router catches a primary
failure and retries once only when a different fallback is configured. Provider
modules and clients are lazy so a missing optional key/provider does not break
unrelated model paths.

### 5.3 Image safety boundary

`validate_image_path()` resolves both the image and allowed frames directory,
requires the image to be a descendant of that directory, permits only JPEG/PNG,
rejects empty files, and enforces `VISION_MAX_IMAGE_MB` (20 MiB by default).
This boundary matters when a future UI passes user-selected paths.

### 5.4 Prompt contract

All providers share the prompt builder. The desired result is JSON only, with
pet detection, one or more activities, confidence, detected registered pet
names, objects, interaction, and a short summary. When pet profiles exist, the
candidate frame is compared to up to two reference photos. A name must only be
returned when visual identity is supported; an unmatched visible cat remains a
generic cat with an empty `name_of_pet` list.

## 6. Pet identity profiles

The pet-profile module is the owner of registered names and reference photos.
It is deliberately independent of a web framework so a future HTTP route or
Electron IPC handler can call it without duplicating validation or storage
logic.

Core invariants:

- at most two profiles;
- names are trimmed, bounded, and unique case-insensitively;
- source images must be valid supported image files within the size limit;
- uploads are copied into managed storage rather than retaining arbitrary
  external paths;
- the manifest stores managed relative filenames and is written atomically;
- model prompts and provider calls receive profiles in manifest order.

Application data lives below `src/data/pet_profiles/` and must not be committed.
The public module API is the seam for a future upload endpoint. The CLI is a
working non-UI way to register/list/remove profiles while no transport exists.

Identity data flows forward as `name_of_pet`, represented as a list because a
frame/event can contain both registered cats. Empty means the model saw no
registered match or no profiles were configured. The event builder unions names
while frames merge; query evidence and highlight captions consume that list.

## 7. Event builder in detail

`event_pipeline.run_event_pipeline()` is the authoritative orchestration order:

1. `clean_results`
2. `normalize_results`
3. `detect_state_changes`
4. `merge_consecutive_events`
5. `score_events`
6. `merge_nearby_events`
7. `generate_event_json`

### 7.1 Clean

`clean_results.py` deep-copies every frame and makes a consistent result shape.
It extracts JSON from fenced markdown or the outermost braces of `raw_output`.
Malformed output becomes `invalid=true`, `pet_detected=false`, confidence zero,
and a diagnostic summary. Objects become dictionaries with a string name and a
numeric confidence. Activities and pet names are sanitized into deduplicated
lists.

### 7.2 Normalize

`normalize_results.py` lowercases and canonicalizes known activity, object, and
interaction aliases. For example, `pawing` maps to `playing`, `kitten` maps to
object `cat`, and `pink bowl` maps to `bowl`. Unknown meaningful values are
retained in normalized underscore form rather than discarded.

Multiple activities stay in one observation/event. A raw multi-action value is
split into a list and each member is normalized independently; the builder does
not create duplicate events solely to represent multiple simultaneous actions.

### 7.3 Candidate conversion and merging

`detect_state_changes.py` drops invalid/no-pet frames and turns every remaining
frame into an event candidate. Candidate time comes from the vision record, so
motion-derived `end_time` survives. It carries activities, names, frames,
thumbnail, objects, interaction, summary, confidence, and state-change status.

`merge_consecutive_events.py` merges adjacent candidates only when their full
activity lists match. It extends the range, concatenates frame names, unions
objects and pet names, keeps the first non-empty interaction, uses the
highest-confidence summary/thumbnail, and keeps max confidence.

`merge_nearby_events.py` performs a second same-activity merge when the gap is
under 20 seconds. This can bridge a short period of missing model evidence. It
keeps the maximum importance score from the merged records.

### 7.4 Importance

`score_events.py` assigns a base from the strongest activity in an event:
playing/jumping are highest, eating/drinking/scratching are medium, and quiet
states are lower. Interaction, multiple identified cats, and very high model
confidence add bonuses. Importance is a highlight-ranking feature, not a model
probability.

### 7.5 Final timeline contract

New timelines are JSON arrays. Every object contains:

```json
{
  "event_id": 1,
  "activities": ["playing", "jumping"],
  "name_of_pet": ["Milo"],
  "start_time": 10.0,
  "end_time": 14.0,
  "duration": 4.0,
  "importance": 10,
  "thumbnail_frame": "frame_demo_000300_10.00s.jpg",
  "objects": ["cat", "toy"],
  "interaction": "toy",
  "summary": "Milo is batting a toy across the floor.",
  "clip_start": 9.0,
  "clip_end": 16.0
}
```

`clip_start` is one second before the event (clamped to zero) and `clip_end` is
two seconds after it. These ranges are the available evidence windows consumed
by query proof and highlight selection.

Readers accept the legacy scalar `activity` field so existing dated timelines
remain queryable/renderable. Writers emit only the plural `activities` field.

### 7.6 Dated storage

`timeline_storage.py` owns all timeline path rules:

- local calendar date -> `final_timeline/YYYY-MM-DD`;
- `<video>_vision.json` -> `<video>_final_timeline.json`;
- a collision adds `_2`, `_3`, etc.;
- `latest_final_timeline()` chooses modification time, then name.

Never hand-roll these filenames in another module. The highlight timeline
router and query repository intentionally reuse these rules.

## 8. Query layer in detail

The query layer is deterministic. It does not send questions or timeline data
to an LLM.

### 8.1 Public API and CLI

The primary API is:

```python
from app.query_layer import answer_query

response = answer_query("Did Milo play today?", include_proof=True)
```

CLI entry point from `src/backend`:

```powershell
python -m app.query_layer "Did Milo play today?" --proof
```

`answer_query()` accepts explicit date/timeline/video/proof/response roots and
an FFmpeg path, making it testable and suitable for a future UI service layer.

### 8.2 Date parsing

`date_parser.py` supports:

- default/today;
- yesterday;
- one ISO date;
- the first two ISO dates as an inclusive range;
- last/past N days;
- explicit start/end parameters, which override words in the question.

Local timezone semantics are intentional because timeline folders use local
calendar dates.

### 8.3 Repository loading

`timeline_repository.py` walks each requested date. For each video stem it keeps
only the newest numeric timeline version, preventing repeated processing from
double-counting events while still loading distinct videos from the same day.
Malformed files/events become warnings instead of aborting unrelated evidence.

Source footage is resolved by the highlight module's video resolver. Missing
footage does not discard timeline evidence: the answer can still be `yes`, but
proof rendering may be unavailable and the event records a resolution error.

The repository sorts events by date, timeline filename, start time, and event
ID. This is the default chronological order before optional relevance ranking.

### 8.4 Intent and reverse normalization

`intent_parser.py` recognizes existence, count, and duration questions. It maps
common question synonyms to canonical activities and objects and detects a
`near` relation. Registered names appearing in the question become an identity
filter, so two-cat households can ask about one pet.

`query_normalization.py` is deliberately the reverse of event normalization.
One intent can be supported by multiple terms across four independent fields:

- activities: weight 0.70;
- summary: weight 0.65;
- interaction: weight 0.35;
- objects: weight 0.25.

An activity needs at least 0.60 points, so a strong activity or summary is
enough, while a toy merely present near a sleeping cat is not enough to claim
play. Objects and relations requested explicitly add requirements and score.
Match reasons record exactly which field/term contributed.

`relevance_score` is this deterministic weighted evidence score. It is an
explainable ranking value, not a calibrated probability or model confidence.

### 8.5 Answer semantics

Statuses are distinct:

- `yes`: usable timeline and at least one match;
- `no`: usable timeline but no match;
- `no_data`: no usable timeline for any requested date;
- `unsupported`: no supported activity/object intent.

Answers report count or summed core-event duration as appropriate. When an
identified name is available, answers use it instead of the generic “your cat.”
Evidence contains the activity list, pet-name list, summary/context, source
paths, proof window, formatted timestamps, relevance score/reasons, and eventual
proof segment number.

Response paths are made repository-relative before persistence. Responses are
atomically archived under:

```text
src/results/query-results/YYYY-MM-DD/proof_requested/
src/results/query-results/YYYY-MM-DD/proof_not_requested/
```

Each uses a UUID-like identifier and never overwrites another response.

### 8.6 Proof ordering and rendering

When proof is requested, matches are ordered by descending relevance score with
stable chronological tie-breakers. Overlapping ranges from the same video/date
are merged without losing the relevance-first segment order. Thus proof segment
1 is the strongest evidence, not simply the earliest timestamp.

Proof rendering normalizes each range to 1280x720, 30 fps, H.264, no audio, then
concatenates it into one MP4. Files live under
`src/results/query-proofs/temp/YYYY-MM-DD` and default to a 24-hour lifetime.
Cleanup only removes managed `*_query_proof.mp4` files. Rendering failure is
contained in the response and does not erase the textual answer.

## 9. Highlight reel in detail

### 9.1 Input routing

`timeline_router.py` chooses an explicit path or today's most recently modified
timeline. `video_resolver.py` strips `_final_timeline` and an optional numeric
collision suffix, then requires exactly one matching supported video extension.
Ambiguity or absence must be resolved with an explicit video path.

### 9.2 Selection

`selector.py` validates numeric event fields and creates candidates. It computes
relative quality from both the raw importance value and the rank of that value
inside the current timeline; there is no fixed global importance threshold.

Greedy selection starts with the strongest event and then balances:

- activity diversity;
- interaction-group diversity;
- object-set diversity;
- temporal coverage;
- overlap penalty;
- a very small core-duration preference.

The result is sorted chronologically before rendering because a highlight reel
is a narrative montage. This differs intentionally from proof video, which is
relevance-first evidence.

`_event_segment()` stays inside the event's available `clip_start`/`clip_end`
window and caps each selected duration (10 seconds by default). Legacy timelines
with wider padding remain supported.

### 9.3 Cinematic captions

Each `HighlightClip` derives a short caption from the summary, uses registered
names when available, and falls back to a readable activity phrase. Captions are
trimmed to subtitle length. The renderer burns the caption into every segment
before concatenation using a centered, white, bordered subtitle over a soft
black translucent box near the lower safe area. Caption text is passed via a
temporary text file rather than interpolated into a shell command.

The manifest records each caption alongside selection score/reasons so UI code
can display the same description independently of the video.

### 9.4 Output

`output_storage.py` creates paired, date-partitioned, non-overwriting paths:

```text
src/results/highlight-reel/YYYY-MM-DD/<video>_highlight_reel[_N].mp4
src/results/highlight-reel/YYYY-MM-DD/<video>_highlight_reel[_N]_manifest.json
```

The manifest is written atomically only after a reel renders successfully.

## 10. Frontend

The frontend uses React 18, Vite 5, and Electron 31.

- `App.jsx`: displays the dashboard beneath a timed splash overlay.
- `SplashScreen`: animated paw trail and logo.
- `Dashboard`: header, date-sorted mock cards, and add-footage modal.
- `AddFootageModal`: drag/drop or file input; keeps a selected browser `File`.
- `FootageCard`: decorative mock thumbnail and localized date.
- `PawIcon`: reusable inline SVG.
- CSS uses global design tokens and BEM-style component class names.

`Dashboard.handleUpload()` currently logs the browser `File`; no backend request
or IPC call occurs. `electron/preload.js` is only a comment, so there is no
exposed bridge. `MOCK_FOOTAGES` is placeholder data. These are real integration
gaps, not domain-module defects.

The Electron main process uses context isolation defaults and loads Vite on
port 5173 in development or `dist/index.html` when packaged. Vite's relative
`base: './'` supports loading the packaged file.

## 11. Configuration and dependencies

Python dependencies are intentionally small:

- OpenCV for video/frame processing;
- Ollama client for local vision;
- python-dotenv for environment loading;
- Google GenAI, Anthropic, and OpenAI provider clients;
- imageio-ffmpeg as an FFmpeg fallback.

Provider keys belong in `src/backend/.env`, which is ignored. `.env.example`
contains names and non-secret defaults only. Never commit a populated `.env`.

Frontend dependencies are React/ReactDOM with Vite, the React plugin, and
Electron as development dependencies. The npm lockfile is the reproducible
source of exact JavaScript versions.

FFmpeg resolution order is explicit CLI path, system `PATH`, then the
`imageio-ffmpeg` bundled executable. Video rendering always invokes subprocesses
with argument lists (`shell=False`), not shell-built command strings.

## 12. Coding style and conventions

### Python

- Four-space indentation and conventional `snake_case` functions/variables.
- Module constants use `UPPER_SNAKE_CASE`.
- Small, focused modules; orchestration files call pure-ish transformation
  stages rather than mixing all behavior into one function.
- Public functions have concise docstrings; comments explain design reasons and
  invariants, not line-by-line syntax.
- `pathlib.Path` is the path abstraction. Convert to strings only at external
  libraries, subprocess arguments, or JSON boundaries.
- Dependency injection uses optional path/date/time/FFmpeg arguments. Preserve
  this: tests rely on temporary roots and deterministic dates.
- Filesystem writers create parent directories, avoid accidental overwrite
  where history matters, and use temporary-file replacement for atomic JSON.
- Domain failures raise `ValueError`, `FileNotFoundError`, or `RuntimeError` with
  actionable messages. The query service intentionally converts proof failures
  to structured response errors.
- Dataclasses are used for immutable domain records crossing modules.
- Avoid provider imports at module import time when a missing package/key should
  not affect other providers.
- Backward compatibility belongs at read boundaries. Writers use the newest
  schema; readers accept legacy scalar `activity` timelines.

### React/CSS

- Function components and named default exports.
- Local UI state with hooks; no state library.
- Single quotes, no semicolons, trailing commas where already used.
- Component CSS imported beside the JSX file.
- BEM-like class names (`component__part`, `component--modifier`).
- Shared colors/shadows/radius are CSS custom properties in `global.css`.
- Buttons include accessible labels when the visible glyph is not descriptive.

### JSON and paths

- Human-facing JSON uses four-space indentation in backend artifact writers;
  benchmark logs use two spaces.
- Time values are seconds as numbers; formatted query timestamps use
  `HH:MM:SS.mmm` and do not wrap after 24 hours.
- Dates and date folders are ISO `YYYY-MM-DD` in local time.
- Stored response paths should be forward-slash repository-relative paths.
- Artifact filenames include the source-video stem and use numeric suffixes for
  collisions.

## 13. Testing strategy

The suite uses `unittest`, temporary directories, and mocks only where a real
FFmpeg render would make a unit test slow or environment-dependent.

Run from `src/backend`:

```powershell
python -m unittest discover -s tests -v
```

Coverage areas include:

- timeline date/naming/collision rules and raw-input preservation;
- highlight selection, legacy timeline compatibility, router, and video lookup;
- date and intent parsing, reverse normalization, false-positive prevention;
- multi-video/date repository loading and missing-video behavior;
- proof range merging, lifecycle cleanup, response storage, and service contract;
- grouped activity output and asymmetric evidence padding;
- pet-profile limits/validation and dynamic prompt identity instructions;
- relevance-first proof ordering;
- caption generation and safe FFmpeg filter construction.

Before a change is complete, run the full Python suite, Python bytecode
compilation, and the frontend production build. For media changes, also render a
real short reel when the local FFmpeg build supports the required filters and
inspect the output/manifest.

## 14. Key invariants to preserve in future work

1. Do not make a missing date look like a negative pet-activity answer.
2. Do not discard queryable JSON evidence merely because source video is gone.
3. Do not double-count older numeric timeline versions for one video/day.
4. Do not overwrite raw vision history assumptions: raw is overwrite-in-place;
   final timeline/results are collision-safe history.
5. Do not infer a registered pet name when the vision model is uncertain.
6. Keep `name_of_pet` and `activities` list-shaped even for one item.
7. Keep query match reasons and relevance deterministic/explainable.
8. Proof montage order is relevance-first; highlight montage order is
   chronological after diversity selection.
9. Keep filesystem and time roots injectable for tests and future UI services.
10. Never pass a user-controlled string through a shell command.
11. Treat reference photos, source footage, frames, timelines, and rendered
    clips as potentially private user data.
12. Update `tasks.md` and this guide whenever a contract or flow changes.

## 15. Practical entry points

From `src/backend` unless noted:

```powershell
# motion candidates
python -m app.motion_detector.main_stream_worker <video-path>

# vision analysis (provider arguments are optional)
python app/vision_model/main_run_on_candidates.py <video-stem> [primary] [fallback]

# final dated timeline
python -m app.event_builder.main_event_tracker <video-stem>

# deterministic query
python -m app.query_layer "Did my cat play today?" --proof

# highlight reel
python -m app.highlight_reel --max-clips 5 --max-clip-seconds 10

# frontend (from src/frontend)
npm run dev
npm run build
npm run electron
```

For programmatic work, prefer public functions over spawning these CLIs. CLIs
are thin adapters for humans; domain behavior belongs in importable services.

