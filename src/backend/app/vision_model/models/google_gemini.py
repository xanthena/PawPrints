"""
google_gemini.py

Communicates with Google's Gemini Vision model. Defaults to the Gemini
Developer API (AI Studio) with a plain API key -- that's the path
judges/teammates use. Set GEMINI_AUTH_MODE=vertex to switch to Vertex AI
+ Application Default Credentials instead, e.g. to test against a GCP
account's free credits when the AI Studio free tier won't allow calls.
"""

import time
from google import genai
from google.genai import types

from prompt import SYSTEM_PROMPT

from config import GEMINI_API_KEY, GEMINI_AUTH_MODE, GOOGLE_PROJECT_ID
from image_validation import validate_image_path

_client = None


def _get_client():
    # Built lazily, not at import time, so importing this module (e.g. from
    # a router that also supports the local model) doesn't fail just
    # because Gemini isn't configured in this environment.
    global _client
    if _client is not None:
        return _client

    if GEMINI_AUTH_MODE == "vertex":
        if not GOOGLE_PROJECT_ID:
            raise RuntimeError("GOOGLE_PROJECT_ID is not set. Add it to your .env file for Vertex AI auth.")
        _client = genai.Client(vertexai=True, project=GOOGLE_PROJECT_ID, location="global")
    elif GEMINI_AUTH_MODE == "api_key":
        if not GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY is not set. Add it to your .env file.")
        _client = genai.Client(api_key=GEMINI_API_KEY)
    else:
        raise ValueError(f"GEMINI_AUTH_MODE must be 'api_key' or 'vertex', got {GEMINI_AUTH_MODE!r}")

    return _client


def analyze(image_path: str, allowed_dir: str) -> str:
    client = _get_client()
    image = validate_image_path(image_path, allowed_dir)

    print("\n" + "=" * 60)
    print("Gemini Analysis Started")
    print("=" * 60)

    print(f"Image : {image.name}")
    print(f"Start Time : {time.strftime('%H:%M:%S')}")

    start = time.perf_counter()

    print("\nSending request to Gemini...")

    with open(image.path, "rb") as f:
        image_bytes = f.read()

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            SYSTEM_PROMPT,
            types.Part.from_bytes(
                data=image_bytes,
                mime_type=image.mime_type,
            ),
        ],
    )

    inference_time = time.perf_counter() - start

    print("Response received!")
    print(f"End Time   : {time.strftime('%H:%M:%S')}")
    print(f"Inference Time : {inference_time:.2f} seconds")

    output = response.text

    print(f"Characters Generated : {len(output)}")

    print("=" * 60)

    return output