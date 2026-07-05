"""
model_router.py

Picks which vision model to call: Gemini, Claude, OpenAI, or a local
model via Ollama (any model Ollama is serving, not just Qwen -- see
OLLAMA_MODEL). Two config knobs control this, mirrored by explicit
function arguments a future API/UI toggle can call through:

- VISION_MODEL_PRIMARY (or `primary=`): which model to try first.
  Defaults to "qwen", the one path guaranteed to need no API key.
- VISION_MODEL_FALLBACK (or `fallback=`): which model to try if the
  primary call raises anything at all -- a rate limit, a missing key,
  a missing package, or any other failure. Defaults to "qwen" too, so
  a fresh clone with nothing configured still works even if the
  primary (e.g. gemini) isn't set up. Set it equal to primary, or to
  "" / unset with no default, to disable fallback entirely.

Gemini and Qwen are the two paths actually tested end-to-end; Claude
and OpenAI are wired up the same way but not yet verified against a
real key.
"""

import os

from models import local_qwen

GEMINI = "gemini"
QWEN = "qwen"
CLAUDE = "claude"
OPENAI = "openai"
_VALID_MODELS = {GEMINI, QWEN, CLAUDE, OPENAI}

DEFAULT_PRIMARY = QWEN
DEFAULT_FALLBACK = QWEN


def _resolve(value, env_var, default):
    resolved = value if value is not None else os.getenv(env_var, default)
    if not resolved:
        return None

    resolved = resolved.strip().lower()
    if resolved not in _VALID_MODELS:
        raise ValueError(f"{env_var} must be one of {_VALID_MODELS}, got {resolved!r}")
    return resolved


def _call(model_name, image_path, allowed_dir):
    if model_name == QWEN:
        return local_qwen.analyze(image_path, allowed_dir)

    if model_name == CLAUDE:
        from models import anthropic_claude  # imported lazily: a missing
        return anthropic_claude.analyze(image_path, allowed_dir)  # package/key shouldn't break other models

    if model_name == OPENAI:
        from models import openai_gpt
        return openai_gpt.analyze(image_path, allowed_dir)

    from models import google_gemini
    return google_gemini.analyze(image_path, allowed_dir)


def analyze(image_path: str, allowed_dir: str, primary: str = None, fallback: str = None) -> dict:
    """
    Returns {"output": <raw model text>, "model_used": "gemini"|"qwen"|
    "claude"|"openai", "fell_back": bool}. Tries `primary` (or
    VISION_MODEL_PRIMARY) first; if that call raises anything and a
    different `fallback` (or VISION_MODEL_FALLBACK) is configured,
    retries once with it.
    """
    primary_model = _resolve(primary, "VISION_MODEL_PRIMARY", DEFAULT_PRIMARY)
    fallback_model = _resolve(fallback, "VISION_MODEL_FALLBACK", DEFAULT_FALLBACK)

    if primary_model is None:
        raise ValueError("No primary model configured (VISION_MODEL_PRIMARY or primary=).")

    try:
        output = _call(primary_model, image_path, allowed_dir)
        return {"output": output, "model_used": primary_model, "fell_back": False}
    except Exception as exc:
        if fallback_model and fallback_model != primary_model:
            print(f"{primary_model} call failed ({exc}); falling back to {fallback_model}.")
            output = _call(fallback_model, image_path, allowed_dir)
            return {"output": output, "model_used": fallback_model, "fell_back": True}
        raise
