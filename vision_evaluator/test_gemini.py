import os
import json
import time

from models.google_gemini import analyze
from timestamp_extractor_from_file import timestamp_extractor_from_file

frames_folder = r"C:\Users\rizla\Documents\kitty-hacks\cat-videos\resized_imgs"

# Folder to save outputs
output_folder = r"C:\Users\rizla\Documents\kitty-hacks\PawPrints\jsons"
os.makedirs(output_folder, exist_ok=True)

output_file = os.path.join(output_folder, "gemini.json")

# Collect all resized images
frames = sorted([
    os.path.join(frames_folder, file)
    for file in os.listdir(frames_folder)
    if file.startswith("frame_")
    and file.lower().endswith((".jpg", ".jpeg", ".png"))
])

results = []


start_clock = time.strftime("%H:%M:%S")
start_timer = time.perf_counter()


for frame in frames:

    print("=" * 80)
    print(f"Analyzing: {os.path.basename(frame)}")
    print(frame)

    result = analyze(frame)

    # If Gemini returns a JSON string, convert it
    if isinstance(result, str):
        try:
            result = json.loads(result)
        except Exception:
            result = {"raw_output": result}

    frame_number, timestamp = timestamp_extractor_from_file(
        os.path.basename(frame)
    )

    results.append({
        "frame": os.path.basename(frame),
        "timestamp": timestamp,
        "frame_number": frame_number,
        "result": result
    })

num_frames = len(frames)
end_clock = time.strftime("%H:%M:%S")
total_time = time.perf_counter() - start_timer

print("\n" + "=" * 80)
print(f"Full VM process started at : {start_clock}")
print(f"Finished at      : {end_clock}")
print(f"Frames Processed : {num_frames}")
print(f"Total Time       : {total_time:.2f} seconds")
print(f"Average / Frame  : {total_time / num_frames:.2f} seconds")
print("=" * 80)


# Replace existing file every run
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=4, ensure_ascii=False)

print("\n" + "=" * 80)
print(f"Saved {len(results)} results to:")
print(output_file)
print("=" * 80)
print(f"Full parsing ends at : {time.strftime('%H:%M:%S')}")