SYSTEM_PROMPT = """
Analyze this CCTV image of a pet.

Return ONLY valid JSON.

{
    "pet_detected": true,
    "activity": "",
    "activity_confidence": 0.0,
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
- Keep activity to one or two words.
- Summary must be one short sentence but add details.
"""