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
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.pet_profiles import list_pet_profiles

if __package__:
    from . import identity_matcher
    from .models import local_ollama
    from .prompt import build_system_prompt
else:
    import identity_matcher
    from models import local_ollama
    from prompt import build_system_prompt

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


def _call(model_name, image_path, allowed_dir, prompt, ollama_model=None):
    if model_name == QWEN:
        return local_ollama.analyze(
            image_path, allowed_dir, prompt, ollama_model=ollama_model
        )

    if model_name == CLAUDE:
        if __package__:
            from .models import anthropic_claude
        else:
            from models import anthropic_claude
        return anthropic_claude.analyze(image_path, allowed_dir, prompt)

    if model_name == OPENAI:
        if __package__:
            from .models import openai_gpt
        else:
            from models import openai_gpt
        return openai_gpt.analyze(image_path, allowed_dir, prompt)

    if __package__:
        from .models import google_gemini
    else:
        from models import google_gemini
    return google_gemini.analyze(image_path, allowed_dir, prompt)


def _outcome(output, model_used, fell_back, matched_names):
    return {
        "output": output,
        "model_used": model_used,
        "fell_back": fell_back,
        "registered_pet_names": matched_names,
    }


def analyze(
    image_path: str,
    allowed_dir: str,
    primary: str = None,
    fallback: str = None,
    pet_profiles=None,
    ollama_model=None,
) -> dict:
    """
    Returns {"output": <raw model text>, "model_used": "gemini"|"qwen"|
    "claude"|"openai", "fell_back": bool, "registered_pet_names": [...]}.
    Tries `primary` (or
    VISION_MODEL_PRIMARY) first; if that call raises anything and a
    different `fallback` (or VISION_MODEL_FALLBACK) is configured,
    retries once with it.

    `ollama_model` picks which locally-served model the "qwen" path
    actually calls (default: OLLAMA_MODEL) -- named "qwen" for the
    provider family, but Ollama can serve any vision-capable model the
    user has pulled, not just Qwen.

    Identity ("which registered pet is this") is decided separately from
    the vision-LLM call, by CLIP visual similarity against each pet's
    reference photos (see identity_matcher.py) -- the LLM only describes
    the scene and always reports an empty name_of_pet itself.
    """
    primary_model = _resolve(primary, "VISION_MODEL_PRIMARY", DEFAULT_PRIMARY)
    fallback_model = _resolve(fallback, "VISION_MODEL_FALLBACK", DEFAULT_FALLBACK)
    profiles = list_pet_profiles() if pet_profiles is None else list(pet_profiles)
    prompt = build_system_prompt(profiles)
    matched_names = identity_matcher.match_identity(image_path, profiles)

    if primary_model is None:
        raise ValueError("No primary model configured (VISION_MODEL_PRIMARY or primary=).")

    try:
        output = _call(primary_model, image_path, allowed_dir, prompt, ollama_model)
        return _outcome(output, primary_model, False, matched_names)
    except Exception as exc:
        if fallback_model and fallback_model != primary_model:
            print(f"{primary_model} call failed ({exc}); falling back to {fallback_model}.")
            output = _call(fallback_model, image_path, allowed_dir, prompt, ollama_model)
            return _outcome(output, fallback_model, True, matched_names)
        raise
