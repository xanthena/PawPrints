# Reverse query normalization

`query_normalization.py` expands conversational questions back toward the
different evidence forms that may appear in a final timeline.

For example, a canonical `playing` query can be supported by:

- `playing`, `pawing`, `chasing`, or `zoomies` in `activities`
- `playful`, `toying around`, `running around`, or `zoomies` in `summary`
- `toy`, `ball`, `wand`, or `rope toy` in `interaction`
- matching toy terms in `objects`

The matcher scores `activities`, `summary`, `objects`, and `interaction`
independently. Strong activity/summary evidence can match by itself, while
weaker context generally needs support from more than one field. A sleeping
cat with only a toy object nearby is therefore not reported as playing.

Every result includes `match_reasons`, such as:

```json
[
    "activity.playing.summary:playful",
    "activity.playing.interaction:toy",
    "activity.playing.objects:toy"
]
```

The same reverse-normalization structure covers eating, drinking, running,
jumping, sleeping, scratching, grooming, walking, approaching, looking out,
and common object aliases such as sofa/couch.
