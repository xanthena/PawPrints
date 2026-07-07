"""
identity_matcher.py

Determines which registered pet (if any) is visible in a candidate frame
by CLIP visual similarity against each pet's reference photos, instead of
asking the vision-LLM to guess identity from the same call that describes
the scene. The LLM was prone to hallucinating descriptive labels ("Orange
Tabby Cat") and conflating candidate + reference images into one combined
description -- this makes identity a separate, deterministic signal.

The CLIP model and every embedding computed from it are cached at module
level (loaded once per process, same lazy-singleton pattern as the hosted
API clients in models/*.py) since re-embedding the same handful of
reference photos on every candidate frame would be wasted work.
"""

from pathlib import Path

_model = None
_preprocess = None


def _get_model():
    # Built lazily, not at import time, so importing this module doesn't
    # pull in torch/open_clip (and pay the one-time model-load cost) for
    # code paths that never need identity matching.
    global _model, _preprocess
    if _model is not None:
        return _model, _preprocess

    import open_clip

    # The "-quickgelu" variant matches the activation function the
    # "openai" pretrained weights were actually trained with; the plain
    # "ViT-B-32" tag silently mismatches it (open_clip warns about this)
    # and would degrade embedding quality.
    _model, _, _preprocess = open_clip.create_model_and_transforms(
        "ViT-B-32-quickgelu", pretrained="openai"
    )
    _model.eval()
    return _model, _preprocess


_detector = None

# Fraction of the detected box's own width/height added as padding on
# each side before cropping -- a tight, exact crop can clip an ear, tail,
# or paw at the boundary, which would remove real coat-pattern signal
# right where it's most useful for telling two pets apart.
DETECTION_PADDING_RATIO = 0.15


def _get_detector():
    # Same lazy-singleton pattern as _get_model() -- this is a separate,
    # much smaller model (YOLOv8n, pretrained on COCO) used only to find
    # where the cat is in a frame before CLIP embeds it, not to describe
    # the scene (that stays the vision-LLM's job, on the full frame).
    global _detector
    if _detector is not None:
        return _detector

    from ultralytics import YOLO

    _detector = YOLO("yolov8n.pt")
    return _detector


def _detect_cat_box(path, image_size):
    """Return the highest-confidence "cat" bounding box in the image, in
    (left, upper, right, lower) pixel coordinates padded by
    DETECTION_PADDING_RATIO and clamped to the image bounds, or None if
    no cat was detected."""
    detector = _get_detector()
    results = detector(str(path), verbose=False)
    boxes = results[0].boxes
    names = results[0].names

    best = None
    for box in boxes:
        if names[int(box.cls[0])] != "cat":
            continue
        confidence = float(box.conf[0])
        if best is None or confidence > best[0]:
            best = (confidence, box.xyxy[0].tolist())
    if best is None:
        return None

    left, upper, right, lower = best[1]
    pad_x = (right - left) * DETECTION_PADDING_RATIO
    pad_y = (lower - upper) * DETECTION_PADDING_RATIO
    width, height = image_size
    return (
        max(0, left - pad_x),
        max(0, upper - pad_y),
        min(width, right + pad_x),
        min(height, lower + pad_y),
    )


# {(resolved_path_str, mtime_ns): embedding} -- keyed on mtime as well as
# path so a photo replaced or appended via add_image() during a running
# process is picked up automatically, without needing a cache-invalidation
# hook wired into pet_profiles/store.py.
_embedding_cache = {}

MATCH_THRESHOLD = 0.90
# Empirical placeholder, not derived from a labeled dataset -- there isn't
# one, just a handful of reference photos per pet. Tune this constant
# against real footage; it is intentionally not exposed as an env var or
# UI setting, since it's a tuning knob for whoever's calibrating the
# matcher, not a user-facing feature.
#
# Calibrated against real footage *with cropping enabled* (see
# _detect_cat_box): once the shared-background confound is removed, a
# genuine match reliably scores ~0.94-0.97, while every other case --
# the wrong registered pet in the same real video, or a completely
# unregistered cat -- clusters around ~0.75-0.85. 0.90 sits in the gap
# between those two bands. Before cropping, real matches and wrong-pet
# scores were separated by only ~0.01-0.03, which is why this constant
# and TOP_MATCH_MARGIN both moved considerably once cropping landed --
# recalibrate both together if either the detector or the embedding
# model ever changes, since they were tuned as a pair against the same
# test frames.
TOP_MATCH_MARGIN = 0.05
# With cropping, a genuine match's gap over the wrong pet in the same
# real video was consistently >0.10 across every test frame observed,
# so 0.05 has real headroom -- a second pet is only added when it's
# genuinely close to the top score (a plausible two-cats-in-frame case),
# not merely because it also cleared MATCH_THRESHOLD independently.


def embed_image(path):
    """Load an image, crop it to the detected cat (if any), run the crop
    through CLIP, and return an L2-normalized embedding vector.

    Cropping first matters because a whole-frame embedding picks up
    background/lighting/composition almost as strongly as coat pattern --
    two pets photographed in similar settings can end up more similar to
    each other than either is to a real match. This crop is only ever
    used for identity embedding; the vision-LLM call that describes the
    scene still sees the original, uncropped frame, since it genuinely
    needs the surrounding context (what the cat is near, interacting
    with, etc).

    Falls back to the full frame if no cat is detected, rather than
    failing -- a missed detection should degrade to today's behavior,
    not break identity matching entirely.
    """
    import torch
    from PIL import Image

    model, preprocess = _get_model()
    image = Image.open(path).convert("RGB")
    box = _detect_cat_box(path, image.size)
    if box is not None:
        image = image.crop(box)

    tensor = preprocess(image).unsqueeze(0)
    with torch.no_grad():
        features = model.encode_image(tensor)
        features = features / features.norm(dim=-1, keepdim=True)
    return features.squeeze(0).numpy()


def _cached_embedding(path):
    resolved = Path(path).expanduser().resolve(strict=True)
    key = (str(resolved), resolved.stat().st_mtime_ns)
    embedding = _embedding_cache.get(key)
    if embedding is None:
        embedding = embed_image(resolved)
        _embedding_cache[key] = embedding
    return embedding


def _cosine_similarity(a, b):
    return float((a * b).sum())


def _profile_name(profile):
    return str(profile["name"] if isinstance(profile, dict) else profile.name)


def _profile_image_paths(profile):
    if isinstance(profile, dict):
        paths = profile.get("image_paths") or profile.get("reference_images")
        if paths:
            return list(paths)
        single = profile.get("image_path") or profile.get("reference_image")
        return [single] if single else []
    return list(profile.image_paths)


def match_identity(candidate_image_path, pet_profiles):
    """Compare the candidate frame against every registered pet's
    reference photos and return the matching name(s), highest similarity
    first.

    A pet's score is the best (max) similarity across all of its
    reference photos, not just its first one, so pets with several
    photos on file get to put their best match forward.

    Decision is relative, not just an absolute per-pet threshold: the
    top-scoring pet must clear MATCH_THRESHOLD, and any other pet is only
    included if its score is within TOP_MATCH_MARGIN of the top one (see
    that constant's comment for why an absolute threshold alone isn't
    enough to tell two different registered pets apart).
    """
    candidate_embedding = _cached_embedding(candidate_image_path)

    scored = []
    for profile in pet_profiles:
        image_paths = _profile_image_paths(profile)
        if not image_paths:
            continue
        best_similarity = max(
            _cosine_similarity(candidate_embedding, _cached_embedding(path))
            for path in image_paths
        )
        scored.append((best_similarity, _profile_name(profile)))

    if not scored:
        return []

    scored.sort(key=lambda item: item[0], reverse=True)
    top_similarity, top_name = scored[0]
    if top_similarity < MATCH_THRESHOLD:
        return []

    return [
        name
        for similarity, name in scored
        if similarity >= top_similarity - TOP_MATCH_MARGIN
    ]
