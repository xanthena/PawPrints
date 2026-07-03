import cv2 as cv
import os


def extract_frames(
    video_path: str,
    output_folder: str,
    interval_seconds: int
):
    """
    Extracts one frame every `interval_seconds` seconds.

    Naming convention:
    frame_000180_6.00s.jpg

    where:
        000180 -> original frame number
        6.00s  -> timestamp in seconds
    """

    vid = cv.VideoCapture(video_path)

    if not vid.isOpened():
        print("Error opening video!")
        return

    frame_count = int(vid.get(cv.CAP_PROP_FRAME_COUNT))
    fps = vid.get(cv.CAP_PROP_FPS)

    print(f"Frames : {frame_count}")
    print(f"FPS    : {fps:.2f}")

    os.makedirs(output_folder, exist_ok=True)

    step = int(fps * interval_seconds)

    for frame_number in range(0, frame_count, step):

        vid.set(cv.CAP_PROP_POS_FRAMES, frame_number)

        ret, frame = vid.read()

        if not ret:
            break

        timestamp = frame_number / fps

        filename = f"frame_{frame_number:06d}_{timestamp:.2f}s.jpg"

        cv.imwrite(
            os.path.join(output_folder, filename),
            frame
        )

    vid.release()

    print("\nFrame extraction complete!")