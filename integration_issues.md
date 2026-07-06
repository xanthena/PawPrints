# UI Integration Issues

This report contains only concrete issues found while tracing the current
React/Electron and Python flows. The backend domain modules work independently;
these items are the missing or risky seams a UI integration must address.

## 1. There is no frontend-to-backend transport

`src/frontend/electron/preload.js` exposes no IPC API, and
`Dashboard.handleUpload()` only writes the selected browser `File` to the
developer console. There is also no Python HTTP server or long-lived worker.
Consequently the current UI cannot register pet photos, ingest footage, check
job progress, query timelines, or play generated result paths.

Recommended boundary: keep the new importable Python services as domain code
and add one thin transport layer. For a local-only Electron product, a preload
bridge can call a supervised Python worker with a small JSON protocol. A local
HTTP API is also reasonable, but it needs loopback binding, authentication or a
per-launch secret, request-size limits, and lifecycle management. Do not make
React reproduce timeline naming, profile limits, or proof ranking rules.

## 2. A selected browser file is not yet an ingested source video

Downstream video resolution assumes footage is stored at
`src/data/source_video/<timeline-video-stem>.<extension>`. The add-footage modal
holds a browser `File`, but nothing validates it, copies it into managed
storage, assigns a collision-safe identity, or records the original filename.
Passing an arbitrary path directly would also conflict with the existing image
path safety model.

Add one ingestion service that validates extension/MIME/size, creates a stable
video/job ID, copies the file into an application-data directory, and returns
that ID to the UI. All later motion, vision, timeline, query, and highlight
calls should use the same ID/stem.

## 3. Runtime storage is tied to the repository layout

Most default paths are derived from `Path(__file__)` and write below `src/data`
or `src/results`. That works in a development checkout but packaged Electron
application resources may be read-only, replaced on upgrade, or shared between
users. User reference photos, videos, frames, timelines, query responses, and
rendered media need an injectable per-user application-data root. The existing
functions already accept many custom roots; centralizing these roots in one
runtime settings object is safer than changing each module independently.

## 4. Motion event persistence appends across reruns

`motion_detector.main_stream_worker.persist_event()` opens
`events.jsonl` in append mode. Starting the same video stem again can retain old
candidates and cause duplicate vision calls unless the integration deletes or
versions the previous job folder. The UI needs job-scoped event directories or
an explicit overwrite/resume policy before it exposes a retry button.

## 5. Long-running work has no job lifecycle

Motion scanning, model inference, FFmpeg rendering, and full-video processing
are synchronous functions/CLIs. A UI call would appear frozen without a job
queue or worker protocol. There is no current progress schema, cancellation,
retry state, partial-failure state, or concurrency limit. Vision inference also
prints progress rather than publishing structured progress events.

Introduce a small job record (`queued`, `running`, stage/progress, `completed`,
`failed`, `cancelled`) and ensure only controlled worker processes mutate one
job's artifacts. Provider errors and proof/highlight rendering errors should be
returned as structured job errors, not parsed from console output.

## 6. Concurrent writers are not locked

Timeline, highlight, response, and profile writers avoid overwrite by checking
for a free filename and then writing. Those checks are safe in one process but
two simultaneous UI jobs can choose the same path before either creates it.
The pet-profile two-item limit has the same read-check-write race.

If the UI can start concurrent jobs, add per-artifact locks or create files
atomically with exclusive creation. Serialize pet-profile mutations.

## 7. Repository-relative paths are not media URLs

Query responses intentionally return strings such as
`src/results/query-proofs/...mp4`. A browser renderer cannot reliably fetch or
play those paths, and Electron should not expose arbitrary filesystem access.
The bridge/API needs a controlled `artifact_id -> stream/file URL` mapping.
Keep local absolute paths out of renderer-visible JSON.

## 8. The frontend still uses mock discovery and has no detail flow

`MOCK_FOOTAGES` supplies all cards, card buttons have no action, and the UI has
no query form, pet-profile management screen, processing state, error state, or
highlight/proof player. These are expected prototype gaps, but a connector
should replace mock data with one backend list contract rather than reading the
filesystem from React.

## 9. Timeline dates are processing dates, not capture timestamps

Timeline folders use the local date when event building runs. Event timestamps
are offsets inside the video, not wall-clock CCTV timestamps. A UI that labels a
card as “Monday” may therefore display upload/processing day rather than capture
day. The ingestion contract should collect or derive `captured_at` and timezone
if calendar-accurate history is a product requirement.

## 10. Python/provider packaging needs an explicit runtime decision

The frontend lockfile is reproducible, but Python dependencies are not bundled
with Electron and most Python requirements are not pinned. The UI installer
must either ship a tested Python environment plus FFmpeg/Ollama expectations or
connect to a separately managed backend. Provider keys must stay in the backend
process; they must never be exposed through preload or React.

