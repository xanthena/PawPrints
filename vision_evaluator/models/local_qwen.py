import time
import ollama

from prompt import SYSTEM_PROMPT


def analyze(image_path: str) -> str:

    print("\n" + "=" * 60)
    print("Qwen Analysis Started")
    print("=" * 60)

    print(f"Image : {image_path}")
    print(f"Start Time : {time.strftime('%H:%M:%S')}")

    start = time.perf_counter()

    print("\nSending request to Ollama...")

    response = ollama.chat(

        model="qwen2.5vl:3b",
        options={
            "num_ctx": 8192
        },
        messages=[
            {
                "role": "user",
                "content": SYSTEM_PROMPT,
                "images": [image_path]
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