from dataclasses import dataclass
from pathlib import Path

from config import MAX_IMAGE_BYTES


_MIME_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
}


@dataclass(frozen=True)
class ValidatedImage:
    path: Path
    name: str
    mime_type: str
    size_bytes: int


def validate_image_path(image_path: str, allowed_dir: str) -> ValidatedImage:
    if not allowed_dir:
        raise ValueError("allowed_dir is required before analyzing an image.")

    base_dir = Path(allowed_dir).expanduser().resolve(strict=True)
    image = Path(image_path).expanduser().resolve(strict=True)

    if not image.is_file():
        raise ValueError("Image path must point to a file.")

    try:
        image.relative_to(base_dir)
    except ValueError as exc:
        raise ValueError("Image must be inside the allowed frames folder.") from exc

    mime_type = _MIME_TYPES.get(image.suffix.lower())
    if mime_type is None:
        allowed = ", ".join(sorted(_MIME_TYPES))
        raise ValueError(f"Unsupported image type. Allowed extensions: {allowed}.")

    size_bytes = image.stat().st_size
    if size_bytes <= 0:
        raise ValueError("Image file is empty.")
    if size_bytes > MAX_IMAGE_BYTES:
        raise ValueError("Image file exceeds the configured size limit.")

    return ValidatedImage(
        path=image,
        name=image.name,
        mime_type=mime_type,
        size_bytes=size_bytes,
    )