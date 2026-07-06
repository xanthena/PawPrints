# Query response contract

Every query is returned as JSON and automatically archived under the local
execution date:

```text
src/results/query-results/YYYY-MM-DD/proof_requested/
src/results/query-results/YYYY-MM-DD/proof_not_requested/
```

Each response uses a unique `<id>_query_response.json` filename, so any number
of queries can be stored on the same day without overwriting.

Paths exposed by the response are repository-relative, for example:

```json
{
    "source_json_path": "src/data/jsons/final_timeline/2026-07-06/full-cat-video_final_timeline.json",
    "source_video_path": "src/data/source_video/full-cat-video.mp4"
}
```

Evidence intentionally omits internal or redundant fields such as importance,
source filenames duplicated by paths, and event-level timestamps. It retains
the proof clip range, formatted clip timestamps, duration, match reasons, and
proof segment number.

Every `proof` object includes `requested`, `status`, and `error`. Successful
proof paths are relative. Segment objects omit internal source paths and
evidence-index mappings.

CLI responses are archived by default. Use `--no-save-response` for a transient
printed result, or `--response-root` to select another archive root.
