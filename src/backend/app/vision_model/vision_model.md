# Vision Model Guide

The vision model folder turns extracted video frames into frame-by-frame model analysis JSON. The generated JSON is later consumed by the event builder.

## `test_qwen.py`

Runs the local Qwen vision flow. It reads image frames from `src/data/frames`, calls the Qwen adapter for each frame, extracts the timestamp from the filename, and writes results to `src/data/jsons/qwen.json`.

Run it from the `src/backend/app/vision_model` folder:

```powershell
python test_qwen.py
```

## `test_gemini.py`

Runs the Gemini vision flow. It reads image frames from `src/data/frames`, calls the Gemini adapter for each frame, extracts the timestamp from the filename, and writes results to `src/data/jsons/gemini.json`.

Run it from the `src/backend/app/vision_model` folder:

```powershell
python test_gemini.py
```

## `paths.py`

Defines shared data paths for frame input and JSON output. The runners use `FRAMES_DIR` for image input and `JSONS_DIR` for generated model output.

## `prompt.py`

Contains the shared vision prompt. The prompt asks the model to return only JSON with pet detection, activity, confidence, objects, interaction, and summary.

## `config.py`

Loads environment configuration. Gemini authenticates via `GEMINI_AUTH_MODE`: `"api_key"` (default) uses `GEMINI_API_KEY` through the Developer API/AI Studio; `"vertex"` uses `GOOGLE_PROJECT_ID` through Vertex AI + Application Default Credentials instead. Image validation uses `VISION_MAX_IMAGE_MB` to limit image size.

## `image_validation.py`

Validates image paths before sending them to a model. It ensures each image is inside the configured frames folder, uses a supported image extension, is not empty, and does not exceed the configured size limit.

## `timestamp_extractor_from_file.py`

Parses frame filenames such as `frame_000120_4.00s.jpg` and returns the frame number and timestamp.

## `models/local_qwen.py`

Sends a validated image to a local Ollama model, using whichever model `OLLAMA_MODEL` names (defaults to `qwen2.5vl:3b`), and returns the model response text.

## `models/google_gemini.py`

Sends a validated image to Gemini through the Gemini Developer API (AI Studio), authenticated with `GEMINI_API_KEY`, using `gemini-2.5-flash`, and returns the model response text.

## `models/anthropic_claude.py`

Sends a validated image to Claude through the Anthropic Messages API, authenticated with `ANTHROPIC_API_KEY`, using whichever model `ANTHROPIC_MODEL` names, and returns the model response text. Not yet tested against a real key.

## `models/openai_gpt.py`

Sends a validated image to OpenAI through the Chat Completions API, authenticated with `OPENAI_API_KEY`, using whichever model `OPENAI_MODEL` names, and returns the model response text. Not yet tested against a real key.

## `model_router.py`

Picks which of the four adapters above to call, via `VISION_MODEL_PREFERENCE` or an explicit override -- this is what makes the model swappable without touching any other code. If Gemini is preferred and unavailable, it falls back to the local model once; Claude/OpenAI have no such fallback.
