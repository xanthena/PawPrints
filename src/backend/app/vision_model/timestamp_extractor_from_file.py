import os
def timestamp_extractor_from_file(frame):
    filename = os.path.basename(frame)
    # resized_frame_000000_0.00s.jpg

    # Remove extension
    filename = os.path.splitext(filename)[0]
    # resized_frame_000000_0.00s

    # Split by "_"
    parts = filename.split("_")

    frame_number = int(parts[1])

    timestamp = float(parts[2].replace("s", ""))

    print(frame_number)
    print(timestamp)
    return frame_number,timestamp