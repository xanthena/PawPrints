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
    reference_images=(),
    ollama_model=None,
) -> str:
    """`ollama_model` overrides OLLAMA_MODEL for this call -- the hook the
    Settings UI's per-request Ollama model picker calls through, so a
    single running backend can serve requests for whichever local model
    the user actually has pulled, not just the configured default."""
    model = ollama_model or OLLAMA_MODEL
    image = validate_image_path(image_path, allowed_dir)

    # One message per image, each with its own adjacent caption, instead
    # of a single flat images=[...] list next to one shared block of
    # text -- a flat list makes the model correlate array position
    # against a separately written enumeration, which small local models
    # don't reliably do (it tends to describe every supplied image as
    # one combined scene instead of comparing candidate vs. references).
    messages = [
        {
            "role": "user",
            "content": f"{prompt}\n\nCCTV candidate image:",
            "images": [str(image.path)],
        }
    ]
    for reference in reference_images:
        messages.append({
            "role": "user",
            "content": f"Reference photo of {reference['name']}:",
            "images": [str(reference["path"])],
        })

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