import json
import re
from copy import deepcopy


DEFAULT_RESULT = {
    "pet_detected": False,
    "activity": "unknown",
    "confidence": 0.0,
    "interaction": "",
    "summary": "",
    "objects": [],
}


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
            result["activity"] = str(parsed_result.get("activity", "unknown")).strip() or "unknown"
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
