import os

from resize_image import resize_image
from frame_finder import extract_frames

video_path = r"C:\Users\rizla\Documents\kitty-hacks\cat-videos\full-cat-video.mp4"

frames_folder = r"C:\Users\rizla\Documents\kitty-hacks\cat-videos\frames"

# New folder for resized images
resized_folder = r"C:\Users\rizla\Documents\kitty-hacks\cat-videos\resized_imgs"
os.makedirs(resized_folder, exist_ok=True)

extract_frames(video_path, frames_folder, 4)
print("-"*80)

count = 0
for filename in os.listdir(frames_folder):

    # Skip already resized images
    if filename.startswith("resized_"):
        continue

    # Only process image files
    if not filename.lower().endswith((".jpg", ".jpeg", ".png")):
        continue

    image_path = os.path.join(frames_folder, filename)

    print(f"\nProcessing: {filename}")

    resize_image(image_path,resized_folder)

    count += 1

