def build_system_prompt(pet_profiles=()):
    """Build the JSON contract for describing a CCTV candidate frame.

    Identity ("which registered pet is this") is no longer decided here --
    it's determined separately by CLIP visual similarity against each
    pet's reference photos (see identity_matcher.py), since the
    vision-LLM was prone to hallucinating names and conflating candidate
    and reference images into one combined description. The model always
    reports an empty name_of_pet; `pet_profiles` is accepted only for
    backward-compatible call sites and is otherwise unused.
    """
    return """
Analyze the supplied CCTV candidate image of a pet.

Return ONLY valid JSON using exactly this shape:
{
    "pet_detected": true,
    "activities": [""],
    "activity_confidence": 0.0,
    "name_of_pet": [],
    "objects": [
        {
            "name": "",
            "confidence": 0.0
        }
    ],
    "interaction": "",
    "summary": ""
}

Rules:
- No markdown.
- No explanation.
- If no pet is visible, set pet_detected to false.
- Keep each activity to one or two words.
- Put simultaneous activities in one activities list for the same frame.
- name_of_pet must always be an empty JSON list -- identity is determined separately, not by you.
- Summary must be one short sentence but add details.
"""


SYSTEM_PROMPT = build_system_prompt()
