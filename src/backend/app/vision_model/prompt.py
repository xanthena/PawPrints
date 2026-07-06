def _profile_name(profile):
    if isinstance(profile, dict):
        return str(profile.get("name", "")).strip()
    return str(getattr(profile, "name", "")).strip()


def build_system_prompt(pet_profiles=()):
    """Build the JSON contract and optional reference-image identity context."""
    names = [name for profile in pet_profiles if (name := _profile_name(profile))]
    if names:
        reference_lines = "\n".join(
            f"- Reference image {index}: {name}"
            for index, name in enumerate(names, start=1)
        )
        identity_rules = f"""
The first supplied image is the CCTV candidate to analyze.
The later supplied reference images are labeled in this order:
{reference_lines}

Compare coat pattern, face, body markings, and other stable visual features.
Only include a registered name when the visible cat is a confident visual match.
Never guess identity from the scene or from the fact that a profile exists.
Use matched names instead of generic cat/kitten wording in the summary.
"""
    else:
        identity_rules = """
No registered reference cats are available. Return an empty name_of_pet list.
"""

    return f"""
Analyze the supplied CCTV candidate image of a pet.
{identity_rules}
Return ONLY valid JSON using exactly this shape:
{{
    "pet_detected": true,
    "activities": [""],
    "activity_confidence": 0.0,
    "name_of_pet": [],
    "objects": [
        {{
            "name": "",
            "confidence": 0.0
        }}
    ],
    "interaction": "",
    "summary": ""
}}

Rules:
- No markdown.
- No explanation.
- If no pet is visible, set pet_detected to false.
- Keep each activity to one or two words.
- Put simultaneous activities in one activities list for the same frame.
- name_of_pet must always be a JSON list with zero, one, or two registered names.
- Summary must be one short sentence but add details.
"""


SYSTEM_PROMPT = build_system_prompt()
