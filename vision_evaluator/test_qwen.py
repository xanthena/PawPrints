import json
import time

from models.local_qwen import analyze
from paths import FRAMES_DIR, JSONS_DIR, REPO_ROOT
from timestamp_extractor_from_file import timestamp_extractor_from_file

JSONS_DIR.mkdir(parents=True, exist_ok=True)
output_file = JSONS_DIR / "qwen.json"

frames = sorted(
    frame
    for frame in FRAMES_DIR.iterdir()
    if frame.is_file()
    and frame.name.startswith("frame_")
    and frame.suffix.lower() in {".jpg", ".jpeg", ".png"}
) if FRAMES_DIR.exists() else []

results = []

start_clock = time.strftime("%H:%M:%S")
start_timer = time.perf_counter()

for frame in frames:

    print("=" * 80)
    print(f"Analyzing: {frame.name}")
    result = analyze(str(frame), allowed_dir=str(FRAMES_DIR))

    # If analyze() already returns a dictionary, keep this.
    # If it returns a JSON string, convert it.
    if isinstance(result, str):
        try:
            result = json.loads(result)
        except Exception:
            result = {"raw_output": result}

    frame_number, timestamp = timestamp_extractor_from_file(frame.name)

    results.append({
        "frame": frame.name,
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
average_time = total_time / num_frames if num_frames else 0
print(f"Average / Frame  : {average_time:.2f} seconds")
print("=" * 80)

# Replace existing file every run
with output_file.open("w", encoding="utf-8") as f:
    json.dump(results, f, indent=4, ensure_ascii=False)

print("\n" + "=" * 80)
print(f"Saved {len(results)} results to:")
print(output_file.relative_to(REPO_ROOT))
print("=" * 80)
print(f"Full parsing ends at : {time.strftime('%H:%M:%S')}")
