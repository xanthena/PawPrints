"""
model_router.py

Picks which vision model to call: Gemini, Claude, OpenAI, or a local
model via Ollama (any model Ollama is serving, not just Qwen -- see
OLLAMA_MODEL). A caller picks which one to try first -- explicitly via
the `preferred` argument, or via the VISION_MODEL_PREFERENCE env var
otherwise, which is what a future UI toggle would set. Gemini and Qwen
are the two paths actually tested end-to-end; Claude and OpenAI are
wired up the same way but not yet verified against a real key.

If the preferred model is Gemini and it's unavailable (rate limited,
quota exceeded, not configured, or the google-genai package isn't even
installed in this environment), this falls back to the local model
once rather than failing the whole call. Claude and OpenAI don't have
this fallback -- picking them is a direct, unconditional call.
"""

import os

from models import local_qwen

GEMINI = "gemini"
QWEN = "qwen"
CLAUDE = "claude"
OPENAI = "openai"
_VALID_MODELS = {GEMINI, QWEN, CLAUDE, OPENAI}

# HTTP status codes worth failing over on: 429 (rate limit / quota
# exceeded), 503 (overloaded / temporarily unavailable).
FALLBACK_STATUS_CODES = {429, 503}


def _default_preference():
    pref = os.getenv("VISION_MODEL_PREFERENCE", QWEN).strip().lower()
    if pref not in _VALID_MODELS:
        raise ValueError(f"VISION_MODEL_PREFERENCE must be one of {_VALID_MODELS}, got {pref!r}")
    return pref


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


def _gemini_unavailable(exc):
    if isinstance(exc, (ImportError, RuntimeError)):
        return True  # package not installed here, or GEMINI_API_KEY not set

    try:
        from google.genai import errors as genai_errors
    except ImportError:
        return False

    return isinstance(exc, genai_errors.APIError) and exc.code in FALLBACK_STATUS_CODES


def analyze(image_path: str, allowed_dir: str, preferred: str = None) -> dict:
    """
    Returns {"output": <raw model text>, "model_used": "gemini"|"qwen"|
    "claude"|"openai", "fell_back": bool}. Tries `preferred` (or
    VISION_MODEL_PREFERENCE) first; if that's Gemini and the call fails
    for an availability reason, retries once with the local model.
    """
    primary = preferred or _default_preference()
    if primary not in _VALID_MODELS:
        raise ValueError(f"preferred must be one of {_VALID_MODELS}, got {primary!r}")

    try:
        output = _call(primary, image_path, allowed_dir)
        return {"output": output, "model_used": primary, "fell_back": False}
    except Exception as exc:
        if primary == GEMINI and _gemini_unavailable(exc):
            print(f"Gemini unavailable ({exc}); falling back to local Qwen.")
            output = _call(QWEN, image_path, allowed_dir)
            return {"output": output, "model_used": QWEN, "fell_back": True}
        raise
