import json
import re
from copy import deepcopy

from app.pet_profiles import list_pet_profiles


DEFAULT_RESULT = {
    "pet_detected": False,
    "activities": ["unknown"],
    "name_of_pet": [],
    "confidence": 0.0,
    "interaction": "",
    "summary": "",
    "objects": [],
}


def _clean_activities(value):
    """Return one deduplicated list from legacy or list-shaped model output."""
    if isinstance(value, list):
        candidates = value
    elif isinstance(value, str):
        candidates = re.split(r"\s*(?:,|/|&|\band\b)\s*", value)
    elif value is None:
        candidates = []
    else:
        candidates = [value]

    activities = []
    for item in candidates:
        activity = str(item or "").strip()
        if activity and activity not in activities:
            activities.append(activity)
    return activities or ["unknown"]


def _registered_pet_names():
    """Casefolded-name -> canonical-name for every currently registered pet.

    The vision model is prompted to only name a registered pet on a
    confident match, but nothing stops it from hallucinating a generic
    descriptive label ("Orange Tabby Cat") instead of leaving
    name_of_pet empty when it isn't sure. Filtering against the actual
    roster here -- the one place raw model output from every provider
    converges -- is what keeps that from reaching the timeline.
    """
    try:
        return {profile.name.casefold(): profile.name for profile in list_pet_profiles()}
    except Exception:
        return {}


def _clean_pet_names(value, registered=None):
    """Keep identity list-shaped because a frame can contain both pets."""
    if registered is None:
        registered = _registered_pet_names()

    if isinstance(value, list):
        candidates = value
    elif isinstance(value, str):
        candidates = re.split(r"\s*(?:,|&|\band\b)\s*", value)
    else:
        candidates = []

    names = []
    seen = set()
    for item in candidates:
        name = " ".join(str(item or "").strip().split())
        canonical = registered.get(name.casefold())
        if canonical and canonical.casefold() not in seen:
            names.append(canonical)
            seen.add(canonical.casefold())
    return names


def _extract_json_text(raw_output):
    if not isinstance(raw_output, str):
        return None

    fenced = re.search(r"```(?:json)?\s*(.*?)\s*```", raw_output, re.DOTALL)
    if fenced:
        return fenced.group(1)

    start = raw_output.find("{")
    end = raw_output.rfind("}")
    if start != -1 and end != -1 and end > start:
        return raw_output[start:end + 1]

    return raw_output


def _parse_result(result):
    if not isinstance(result, dict):
        return None

    if "raw_output" in result:
        json_text = _extract_json_text(result.get("raw_output"))
        if not json_text:
            return None
        try:
            return json.loads(json_text)
        except json.JSONDecodeError:
            return None

    return result


def _clean_objects(objects):
    if not isinstance(objects, list):
        return []

    cleaned = []
    for item in objects:
        if isinstance(item, dict):
            name = str(item.get("name", "")).strip()
            confidence = item.get("confidence", 0.0)
        else:
            name = str(item).strip()
            confidence = 0.0

        if not name:
            continue

        try:
            confidence = float(confidence)
        except (TypeError, ValueError):
            confidence = 0.0

        cleaned.append({"name": name, "confidence": confidence})

    return cleaned


def clean_results(results):
    """Parse malformed model output and return frames with a consistent result."""
    cleaned_results = []
    registered = _registered_pet_names()

    for frame in results:
        cleaned_frame = deepcopy(frame)
        parsed_result = _parse_result(frame.get("result", {}))

        if parsed_result is None:
            result = DEFAULT_RESULT.copy()
            result["invalid"] = True
            result["summary"] = "Invalid model output."
        else:
            result = DEFAULT_RESULT.copy()
            result["pet_detected"] = bool(parsed_result.get("pet_detected", False))
            activity_value = parsed_result.get(
                "activities",
                parsed_result.get("activity", "unknown"),
            )
            result["activities"] = _clean_activities(activity_value)
            result["name_of_pet"] = _clean_pet_names(
                parsed_result.get("name_of_pet", []), registered
            )
            result["interaction"] = str(parsed_result.get("interaction", "")).strip()
            result["summary"] = str(parsed_result.get("summary", "")).strip()
            result["objects"] = _clean_objects(parsed_result.get("objects", []))

            confidence = parsed_result.get(
                "confidence",
                parsed_result.get("activity_confidence", 0.0),
            )
            try:
                result["confidence"] = float(confidence)
            except (TypeError, ValueError):
                result["confidence"] = 0.0

        cleaned_frame["result"] = result
        cleaned_results.append(cleaned_frame)

    return cleaned_results
