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


def analyze(image_path, allowed_dir, prompt=SYSTEM_PROMPT, reference_images=()) -> str:
    image = validate_image_path(image_path, allowed_dir)
    images = [str(image.path), *(str(item["path"]) for item in reference_images)]

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
                "content": prompt,
                "images": images,
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