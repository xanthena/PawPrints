"""
openai_gpt.py

Communicates with OpenAI's vision-capable models (e.g. gpt-4o) through
the Chat Completions API, authenticated with a plain API key.
"""

import time
import base64
import openai

if __package__:
    from ..config import OPENAI_API_KEY, OPENAI_MODEL
    from ..image_validation import validate_image_path
    from ..prompt import SYSTEM_PROMPT
else:
    from config import OPENAI_API_KEY, OPENAI_MODEL
    from image_validation import validate_image_path
    from prompt import SYSTEM_PROMPT

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


def _image_item(path, mime_type):
    encoded = base64.standard_b64encode(path.read_bytes()).decode("utf-8")
    return {
        "type": "image_url",
        "image_url": {"url": f"data:{mime_type};base64,{encoded}"},
    }


def analyze(image_path, allowed_dir, prompt=SYSTEM_PROMPT) -> str:
    client = _get_client()
    image = validate_image_path(image_path, allowed_dir)

    print("\n" + "=" * 60)
    print(f"OpenAI Analysis Started ({OPENAI_MODEL})")
    print("=" * 60)

    print(f"Image : {image.name}")
    print(f"Start Time : {time.strftime('%H:%M:%S')}")

    start = time.perf_counter()

    print("\nSending request to OpenAI...")

    content = [
        {"type": "text", "text": prompt},
        {"type": "text", "text": "CCTV candidate image:"},
        _image_item(image.path, image.mime_type),
    ]

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
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

    output = response.choices[0].message.content

    print(f"Characters Generated : {len(output)}")

    print("=" * 60)

    return output
