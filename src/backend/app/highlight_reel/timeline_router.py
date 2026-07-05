"""Resolve the final timeline produced by a selected vision model.

The interface mirrors ``vision_model.model_router``: callers may provide an
explicit primary/fallback pair, otherwise environment configuration is used.
This keeps the module ready for an API or UI selector without hard-coding
deployment labels such as ``local`` and ``cloud``.
"""

import os
from pathlib import Path

from .paths import JSONS_DIR


GEMINI = "gemini"
QWEN = "qwen"
CLAUDE = "claude"
OPENAI = "openai"
VALID_MODELS = (GEMINI, QWEN, CLAUDE, OPENAI)

# Preserve the current Gemini behavior when no environment choice is supplied.
DEFAULT_PRIMARY = GEMINI
DEFAULT_FALLBACK = QWEN


def _resolve(value, env_var, default):
    resolved = value if value is not None else os.getenv(env_var, default)
    if not resolved:
        return None

    resolved = resolved.strip().lower()
    if resolved not in VALID_MODELS:
        valid = ", ".join(VALID_MODELS)
        raise ValueError(f"{env_var} must be one of: {valid}; got {resolved!r}.")
    return resolved


def timeline_path_for(model_name, jsons_dir=JSONS_DIR):
    """Return the conventional final timeline path for a model."""
    model = _resolve(model_name, "HIGHLIGHT_MODEL_PRIMARY", DEFAULT_PRIMARY)
    return Path(jsons_dir) / f"final_timeline_{model}.json"


def resolve_timeline(
    primary=None,
    fallback=None,
    timeline_path=None,
    jsons_dir=JSONS_DIR,
):
    """Resolve a usable timeline and report which model artifact was used.

    ``primary`` and ``fallback`` override ``HIGHLIGHT_MODEL_PRIMARY`` and
    ``HIGHLIGHT_MODEL_FALLBACK``. If the highlight-specific variables are not
    set, the matching ``VISION_MODEL_*`` values from the upstream router are
    used. An explicit timeline path bypasses model-based filename resolution,
    which supports model-neutral or externally generated event timelines.
    """
    if timeline_path is not None:
        explicit_path = Path(timeline_path).expanduser().resolve()
        if not explicit_path.is_file():
            raise FileNotFoundError(f"Timeline JSON does not exist: {explicit_path}")
        return {
            "timeline_path": explicit_path,
            "model_used": None,
            "fell_back": False,
        }

    primary_default = os.getenv("VISION_MODEL_PRIMARY", DEFAULT_PRIMARY)
    fallback_default = os.getenv("VISION_MODEL_FALLBACK", DEFAULT_FALLBACK)
    primary_model = _resolve(
        primary,
        "HIGHLIGHT_MODEL_PRIMARY",
        primary_default,
    )
    fallback_model = _resolve(
        fallback,
        "HIGHLIGHT_MODEL_FALLBACK",
        fallback_default,
    )
    if primary_model is None:
        raise ValueError(
            "No primary model configured "
            "(HIGHLIGHT_MODEL_PRIMARY or primary=)."
        )

    primary_path = timeline_path_for(primary_model, jsons_dir)
    if primary_path.is_file():
        return {
            "timeline_path": primary_path.resolve(),
            "model_used": primary_model,
            "fell_back": False,
        }

    if fallback_model and fallback_model != primary_model:
        fallback_path = timeline_path_for(fallback_model, jsons_dir)
        if fallback_path.is_file():
            print(
                f"{primary_model} timeline was not found at {primary_path}; "
                f"falling back to {fallback_model}."
            )
            return {
                "timeline_path": fallback_path.resolve(),
                "model_used": fallback_model,
                "fell_back": True,
            }

    fallback_note = (
        f" Fallback '{fallback_model}' was also unavailable."
        if fallback_model and fallback_model != primary_model
        else " Fallback is disabled."
    )
    raise FileNotFoundError(
        f"No final timeline found for primary model '{primary_model}' at "
        f"{primary_path}.{fallback_note}"
    )
