import os
def timestamp_extractor_from_file(frame):
    filename = os.path.basename(frame)
    # frame_000000_0.00s.jpg or frame_<video_stem>_000000_0.00s.jpg

    # Remove extension
    filename = os.path.splitext(filename)[0]
    # frame_000000_0.00s or frame_<video_stem>_000000_0.00s

    # Split from the right so an optional video-stem prefix (which may
    # itself contain "_") doesn't shift these positions.
    parts = filename.rsplit("_", 2)

    frame_number = int(parts[-2])

    timestamp = float(parts[-1].replace("s", ""))

    print(frame_number)
    print(timestamp)
    return frame_number,timestamp