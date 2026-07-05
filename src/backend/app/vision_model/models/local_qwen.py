import time
import ollama

from prompt import SYSTEM_PROMPT
from image_validation import validate_image_path
from config import OLLAMA_MODEL


def analyze(image_path: str, allowed_dir: str) -> str:
    image = validate_image_path(image_path, allowed_dir)

    print("\n" + "=" * 60)
    print(f"Ollama Analysis Started ({OLLAMA_MODEL})")
    print("=" * 60)

    print(f"Image : {image.name}")
    print(f"Start Time : {time.strftime('%H:%M:%S')}")

    start = time.perf_counter()

    print("\nSending request to Ollama...")

    response = ollama.chat(

        model=OLLAMA_MODEL,
        options={
            "num_ctx": 8192
        },
        messages=[
            {
                "role": "user",
                "content": SYSTEM_PROMPT,
                "images": [str(image.path)]
            }
        ]

    )

    inference_time = time.perf_counter() - start

    print("Response received!")
    print(f"End Time   : {time.strftime('%H:%M:%S')}")
    print(f"Inference Time : {inference_time:.2f} seconds")

    output = response["message"]["content"]

    print(f"Characters Generated : {len(output)}")

    print("=" * 60)

    return output