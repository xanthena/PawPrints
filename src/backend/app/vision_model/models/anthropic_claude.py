"""
anthropic_claude.py

Communicates with Anthropic's Claude vision models through the
Anthropic Messages API, authenticated with a plain API key.
"""

import time
import base64
import anthropic

from prompt import SYSTEM_PROMPT

from config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL
from image_validation import validate_image_path

_client = None


def _get_client():
    # Built lazily, not at import time, so importing this module (e.g. from
    # a router that also supports other models) doesn't fail just because
    # Claude isn't configured in this environment.
    global _client
    if _client is None:
        if not ANTHROPIC_API_KEY:
            raise RuntimeError("ANTHROPIC_API_KEY is not set. Add it to your .env file.")
        _client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    return _client


def analyze(image_path: str, allowed_dir: str) -> str:
    client = _get_client()
    image = validate_image_path(image_path, allowed_dir)

    print("\n" + "=" * 60)
    print(f"Claude Analysis Started ({ANTHROPIC_MODEL})")
    print("=" * 60)

    print(f"Image : {image.name}")
    print(f"Start Time : {time.strftime('%H:%M:%S')}")

    start = time.perf_counter()

    print("\nSending request to Claude...")

    with open(image.path, "rb") as f:
        image_b64 = base64.standard_b64encode(f.read()).decode("utf-8")

    message = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": image.mime_type,
                            "data": image_b64,
                        },
                    },
                    {
                        "type": "text",
                        "text": SYSTEM_PROMPT,
                    },
                ],
            }
        ],
    )

    inference_time = time.perf_counter() - start

    print("Response received!")
    print(f"End Time   : {time.strftime('%H:%M:%S')}")
    print(f"Inference Time : {inference_time:.2f} seconds")

    output = message.content[0].text

    print(f"Characters Generated : {len(output)}")

    print("=" * 60)

    return output
