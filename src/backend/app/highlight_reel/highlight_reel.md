# Highlight reel

This module reads a final event timeline, selects a few strong and varied
moments, cuts them from the source video, and joins them into one MP4.

## Timeline and video lookup

By default, the module looks in the current local-date folder:

```text
src/data/jsons/final_timeline/YYYY-MM-DD/
```

If the folder contains multiple final timeline JSON files, the most recently
modified file is selected. This matches the event builder's dated,
collision-safe output layout. An explicit `--timeline` path bypasses the daily
lookup for backfills or manual runs.

The video stem is preserved in each timeline filename. For example,
`my_cat_final_timeline.json` is matched to `src/data/source_video/my_cat.mp4`
(or another supported video extension). Use `--video` when the source is stored
elsewhere or has a different name. This prevents a timeline from one video
being cut against another video's footage.

## Dated, non-overwriting output

Every reel and manifest is written under the current local date:

```text
src/results/highlight-reel/YYYY-MM-DD/my_cat_highlight_reel.mp4
src/results/highlight-reel/YYYY-MM-DD/my_cat_highlight_reel_manifest.json
```

Nothing is overwritten. Running the highlight module again for the same video
on the same day creates matching `_2`, `_3`, and later MP4/manifest pairs. A
different video uses its own video-based filename. The manifest records both
the timeline date and the highlight output date.

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
python -m app.highlight_reel --timeline C:\path\to\final_timeline_custom.json --video C:\path\to\source_video.mp4
python -m app.highlight_reel --max-clips 4 --max-clip-seconds 8
python -m app.highlight_reel --ffmpeg C:\path\to\ffmpeg.exe
```
