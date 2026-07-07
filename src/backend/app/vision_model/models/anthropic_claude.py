"""
anthropic_claude.py

Communicates with Anthropic's Claude vision models through the
Anthropic Messages API, authenticated with a plain API key.
"""

import time
import base64
import anthropic

if __package__:
    from ..config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL
    from ..image_validation import validate_image_path
    from ..prompt import SYSTEM_PROMPT
else:
    from config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL
    from image_validation import validate_image_path
    from prompt import SYSTEM_PROMPT

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


def _image_block(path, mime_type):
    encoded = base64.standard_b64encode(path.read_bytes()).decode("utf-8")
    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": mime_type,
            "data": encoded,
        },
    }


def analyze(image_path, allowed_dir, prompt=SYSTEM_PROMPT) -> str:
    client = _get_client()
    image = validate_image_path(image_path, allowed_dir)

    print("\n" + "=" * 60)
    print(f"Claude Analysis Started ({ANTHROPIC_MODEL})")
    print("=" * 60)

    print(f"Image : {image.name}")
    print(f"Start Time : {time.strftime('%H:%M:%S')}")

    start = time.perf_counter()

    print("\nSending request to Claude...")

    content = [
        {"type": "text", "text": prompt},
        {"type": "text", "text": "CCTV candidate image:"},
        _image_block(image.path, image.mime_type),
    ]

    message = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": content,
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
