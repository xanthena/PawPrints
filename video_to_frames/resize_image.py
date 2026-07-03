import cv2
import os


def resize_image(input_path, output_path=None, size=768):
    """
    Resizes an image while keeping the aspect ratio.

    Parameters
    ----------
    input_path : str
        Original image path.

    output_path : str
        Where to save resized image.
        If None, creates a file called resized_<originalname>.jpg

    size : int
        Longest side after resizing.
    """

    image = cv2.imread(input_path)

    if image is None:
        raise FileNotFoundError(f"Could not load image: {input_path}")

    height, width = image.shape[:2]

    original_file_size = os.path.getsize(input_path) / 1024  # KB

    # Calculate scale while preserving aspect ratio
    scale = size / max(height, width)

    new_width = int(width * scale)
    new_height = int(height * scale)

    resized = cv2.resize(
        image,
        (new_width, new_height),
        interpolation=cv2.INTER_AREA,
    )

    if output_path is None:
        folder = os.path.dirname(input_path)
        filename = os.path.basename(input_path)

        output_path = os.path.join(
            folder,
            f"resized_{filename}"
        )

    cv2.imwrite(output_path, resized)

    resized_file_size = os.path.getsize(output_path) / 1024  # KB

    print("\n" + "=" * 60)
    print("Image Resize Report")
    print("=" * 60)

    print(f"Input Image      : {input_path}")
    print(f"Output Image     : {output_path}")

    print(f"\nOriginal Resolution : {width} x {height}")
    print(f"Resized Resolution  : {new_width} x {new_height}")

    print(f"\nScale Factor        : {scale:.2f}")

    print(f"\nOriginal File Size  : {original_file_size:.2f} KB")
    print(f"Resized File Size   : {resized_file_size:.2f} KB")

    print("=" * 60 + "\n")

    return output_path