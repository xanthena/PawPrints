import cv2
import os


def resize_image(input_path, output_path=None, size=768):
    """
    Resizes an image while keeping the aspect ratio.

    Parameters
    ----------
    input_path : str
        Original image path.

    output_path : str, optional
        Path where the resized image will be saved.
        Can be either:
            - A full file path (e.g. C:\\images\\resized\\cat.jpg)
            - A directory (e.g. C:\\images\\resized)
            - None (saves as resized_<originalname> in the input folder)

    size : int
        Longest side after resizing.
    """

    # Read image
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

    # Determine output path
    if output_path is None:
        folder = os.path.dirname(input_path)
        filename = os.path.basename(input_path)
        output_path = os.path.join(folder, f"resized_{filename}")

    elif os.path.isdir(output_path):
        filename = os.path.basename(input_path)
        output_path = os.path.join(output_path, filename)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Save image
    success = cv2.imwrite(output_path, resized)

    if not success:
        raise RuntimeError(f"Failed to save image to: {output_path}")

    resized_file_size = os.path.getsize(output_path) / 1024  # KB

    print("\n" + "=" * 60)
    print("Image Resize Report")
    print("=" * 60)

    print(f"Input Image          : {input_path}")
    print(f"Output Image         : {output_path}")

    print(f"\nOriginal Resolution : {width} x {height}")
    print(f"Resized Resolution  : {new_width} x {new_height}")

    print(f"\nScale Factor        : {scale:.2f}")

    print(f"\nOriginal File Size  : {original_file_size:.2f} KB")
    print(f"Resized File Size   : {resized_file_size:.2f} KB")

    print("=" * 60 + "\n")

    return output_path