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

Contains the shared vision prompt. The prompt asks the model to return only
JSON with pet detection, activity, confidence, objects, interaction, and
summary.

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
