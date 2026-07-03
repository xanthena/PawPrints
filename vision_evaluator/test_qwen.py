import os
import json

from models.local_qwen import analyze
from timestamp_extractor_from_file import timestamp_extractor_from_file

frames_folder = r"C:\Users\rizla\Documents\kitty-hacks\cat-videos\frames"

# Folder to save outputs
output_folder = "jsons"
os.makedirs(output_folder, exist_ok=True)

output_file = os.path.join(output_folder, "qwen.json")

# Collect all resized images
frames = sorted([
    os.path.join(frames_folder, file)
    for file in os.listdir(frames_folder)
    if file.startswith("resized_")
    and file.lower().endswith((".jpg", ".jpeg", ".png"))
])

results = []

for frame in frames:

    print("=" * 80)
    print(f"Analyzing: {os.path.basename(frame)}")
    print(frame)

    result = analyze(frame)

    # If analyze() already returns a dictionary, keep this.
    # If it returns a JSON string, convert it.
    if isinstance(result, str):
        try:
            result = json.loads(result)
        except Exception:
            result = {"raw_output": result}

    frame_number,timestamp = timestamp_extractor_from_file (os.path.basename(frame))

    results.append({
        "frame": os.path.basename(frame),
        "timestamp":timestamp,
        "frame_number":frame_number,
        "result": result
    })

# Replace existing file every run
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=4, ensure_ascii=False)

print("\n" + "=" * 80)
print(f"Saved {len(results)} results to:")
print(output_file)
print("=" * 80)