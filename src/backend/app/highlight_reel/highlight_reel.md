# Highlight reel

This module reads a final Gemini or Qwen event timeline, selects a few strong
and varied moments, cuts them from the source video, and joins them into one MP4.

## Input choice

`main_highlight_reel.py` currently uses Gemini by default:

```python
INPUT_MODE = "cloud"
INPUT_OPTIONS = {
    "local": JSONS_DIR / "final_timeline_qwen.json",
    "cloud": JSONS_DIR / "final_timeline_gemini.json",
}
```

Change `INPUT_MODE` to `"local"`, or pass `--input-mode local`, to use Qwen.

## Selection behavior

- Importance is evaluated relative to the scores in the current timeline.
  There is no fixed minimum such as `importance >= 9`.
- Up to five clips are selected by default.
- Each clip is at most ten seconds by default.
- Repeated activities, interactions, objects, overlapping ranges, and nearby
  times are penalized so one repetitive scene does not fill the reel.
- The chosen clips are returned to chronological order before rendering.

## Run

From `src/backend`:

```powershell
python -m pip install -r app/highlight_reel/requirements.txt
python -m app.highlight_reel
```

Useful options:

```powershell
python -m app.highlight_reel --input-mode local
python -m app.highlight_reel --max-clips 4 --max-clip-seconds 8
python -m app.highlight_reel --ffmpeg C:\path\to\ffmpeg.exe
```

The default output directory is `src/results/highlight-reel`, containing:

- `highlight_reel.mp4`
- `highlight_reel_manifest.json`, with selected events, times, scores, and
  reasons for selection.
