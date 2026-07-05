"""
google_gemini.py

Communicates with Google's Gemini Vision model
using Application Default Credentials.
"""

import time
from google import genai
from google.genai import types

from prompt import SYSTEM_PROMPT

from config import GOOGLE_PROJECT_ID

GOOGLE_PROJECT_ID = GOOGLE_PROJECT_ID

# Uses Application Default Credentials automatically
client = genai.Client(
    vertexai=True,
    project=GOOGLE_PROJECT_ID,
    location="global",
)


def analyze(image_path: str) -> str:

    print("\n" + "=" * 60)
    print("Gemini Analysis Started")
    print("=" * 60)

    print(f"Image : {image_path}")
    print(f"Start Time : {time.strftime('%H:%M:%S')}")

    start = time.perf_counter()

    print("\nSending request to Gemini...")

    with open(image_path, "rb") as f:
        image_bytes = f.read()

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            SYSTEM_PROMPT,
            types.Part.from_bytes(
                data=image_bytes,
                mime_type="image/jpeg",
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