# Vision Model Guide

The vision model folder turns extracted video frames into frame-by-frame model
analysis JSON. The generated JSON is later consumed by the event builder.

## `main_run_on_candidates.py`

The real entry point. It reads a video's `events.jsonl` from the motion
detector, skips `burst_end` markers, computes each candidate's real `end_time`,
and calls the configured model through `model_router.py`.

It writes to:

```text
src/data/jsons/<video_stem>_vision.json
```

This raw vision file intentionally uses write mode, so rerunning vision for the
same video overwrites its previous `_vision.json`. Dated, non-overwriting
history begins only after the event-builder stage.

Run it from `src/backend/app/vision_model`:

```powershell
python main_run_on_candidates.py <video_stem> [primary_model] [fallback_model]
```

## `paths.py`

Defines shared data paths for frame input and JSON output.

## `prompt.py`

Builds the shared vision prompt. It asks for grouped activities, `name_of_pet`,
confidence, objects, interaction, and summary. When one or two profiles exist,
all providers receive the CCTV candidate plus labeled reference photos and are
instructed to identify conservatively.

## `config.py`

Loads environment configuration. Gemini authenticates through the configured
API-key or Vertex mode. Image validation uses `VISION_MAX_IMAGE_MB` to limit
image size.

## `image_validation.py`

Validates that images are inside the frames folder, supported, non-empty, and
within the configured size limit.

## `models/local_qwen.py`

Calls the configured local Ollama vision model.

## `models/google_gemini.py`

Calls Gemini through the configured Google authentication mode.

## `models/anthropic_claude.py`

Calls Claude through the Anthropic Messages API.

## `models/openai_gpt.py`

Calls OpenAI through the Chat Completions API.

## `model_router.py`

Selects the primary vision model and retries once with the configured fallback
when needed. Both values can be supplied explicitly or through environment
configuration.

## Pet identity profiles

Profiles are framework-independent and limited to two:

```powershell
python -m app.pet_profiles register Milo C:\path\to\milo.jpg
python -m app.pet_profiles register Luna C:\path\to\luna.png
python -m app.pet_profiles list
python -m app.pet_profiles remove Milo
```

Registered names propagate through raw JSON, timelines, queries, and captions.
