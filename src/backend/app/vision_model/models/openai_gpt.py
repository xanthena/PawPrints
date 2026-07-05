"""
openai_gpt.py

Communicates with OpenAI's vision-capable models (e.g. gpt-4o) through
the Chat Completions API, authenticated with a plain API key.
"""

import time
import base64
import openai

from prompt import SYSTEM_PROMPT

from config import OPENAI_API_KEY, OPENAI_MODEL
from image_validation import validate_image_path

_client = None


def _get_client():
    # Built lazily, not at import time, so importing this module (e.g. from
    # a router that also supports other models) doesn't fail just because
    # OpenAI isn't configured in this environment.
    global _client
    if _client is None:
        if not OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is not set. Add it to your .env file.")
        _client = openai.OpenAI(api_key=OPENAI_API_KEY)
    return _client


def analyze(image_path: str, allowed_dir: str) -> str:
    client = _get_client()
    image = validate_image_path(image_path, allowed_dir)

    print("\n" + "=" * 60)
    print(f"OpenAI Analysis Started ({OPENAI_MODEL})")
    print("=" * 60)

    print(f"Image : {image.name}")
    print(f"Start Time : {time.strftime('%H:%M:%S')}")

    start = time.perf_counter()

    print("\nSending request to OpenAI...")

    with open(image.path, "rb") as f:
        image_b64 = base64.standard_b64encode(f.read()).decode("utf-8")

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": SYSTEM_PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{image.mime_type};base64,{image_b64}"},
                    },
                ],
            }
        ],
    )

    inference_time = time.perf_counter() - start

    print("Response received!")
    print(f"End Time   : {time.strftime('%H:%M:%S')}")
    print(f"Inference Time : {inference_time:.2f} seconds")

    output = response.choices[0].message.content

    print(f"Characters Generated : {len(output)}")

    print("=" * 60)

    return output
