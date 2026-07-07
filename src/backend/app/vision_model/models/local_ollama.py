import time
import ollama

if __package__:
    from ..config import OLLAMA_MODEL
    from ..image_validation import validate_image_path
    from ..prompt import SYSTEM_PROMPT
else:
    from config import OLLAMA_MODEL
    from image_validation import validate_image_path
    from prompt import SYSTEM_PROMPT


def analyze(
    image_path,
    allowed_dir,
    prompt=SYSTEM_PROMPT,
    ollama_model=None,
) -> str:
    """`ollama_model` overrides OLLAMA_MODEL for this call -- the hook the
    Settings UI's per-request Ollama model picker calls through, so a
    single running backend can serve requests for whichever local model
    the user actually has pulled, not just the configured default."""
    model = ollama_model or OLLAMA_MODEL
    image = validate_image_path(image_path, allowed_dir)

    messages = [
        {
            "role": "user",
            "content": f"{prompt}\n\nCCTV candidate image:",
            "images": [str(image.path)],
        }
    ]

    print("\n" + "=" * 60)
    print(f"Ollama Analysis Started ({model})")
    print("=" * 60)

    print(f"Image : {image.name}")
    print(f"Start Time : {time.strftime('%H:%M:%S')}")

    start = time.perf_counter()

    print("\nSending request to Ollama...")

    response = ollama.chat(
        model=model,
        options={
            "num_ctx": 8192
        },
        messages=messages,
    )

    inference_time = time.perf_counter() - start

    print("Response received!")
    print(f"End Time   : {time.strftime('%H:%M:%S')}")
    print(f"Inference Time : {inference_time:.2f} seconds")

    output = response["message"]["content"]

    print(f"Characters Generated : {len(output)}")

    print("=" * 60)

    return output