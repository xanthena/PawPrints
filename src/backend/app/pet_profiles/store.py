"""Validated, atomic local storage for pet identity reference photos."""

import json
import shutil
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_PROFILE_DIR = REPO_ROOT / "src" / "data" / "pet_profiles"
MAX_PETS = 2
MAX_NAME_LENGTH = 40
MAX_IMAGE_BYTES = 20 * 1024 * 1024
SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


@dataclass(frozen=True)
class PetProfile:
    profile_id: str
    name: str
    image_paths: tuple
    created_at: str

    @property
    def image_path(self):
        """The first registered photo -- for callers that only need one."""
        return self.image_paths[0]

    def to_dict(self):
        return {
            "id": self.profile_id,
            "name": self.name,
            "reference_images": [str(path) for path in self.image_paths],
            "created_at": self.created_at,
        }


def _clean_name(value):
    name = " ".join(str(value or "").strip().split())
    if not name:
        raise ValueError("Pet name is required.")
    if len(name) > MAX_NAME_LENGTH:
        raise ValueError(f"Pet name must be at most {MAX_NAME_LENGTH} characters.")
    if any(unicodedata.category(character).startswith("C") for character in name):
        raise ValueError("Pet name cannot contain control characters.")
    return name


def _validate_image(path, max_image_bytes=MAX_IMAGE_BYTES):
    image = Path(path).expanduser().resolve(strict=True)
    if not image.is_file():
        raise ValueError("Reference image path must point to a file.")
    if image.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
        raise ValueError("Reference image must be a JPEG or PNG file.")

    size = image.stat().st_size
    if size <= 0:
        raise ValueError("Reference image is empty.")
    if size > max_image_bytes:
        raise ValueError("Reference image exceeds the configured size limit.")

    with image.open("rb") as file:
        header = file.read(16)
        if image.suffix.lower() == ".png":
            valid = header.startswith(b"\x89PNG\r\n\x1a\n")
        else:
            valid = header.startswith(b"\xff\xd8\xff")
    if not valid:
        raise ValueError("Reference image content does not match its extension.")
    return image


def _image_files(record):
    """Read a manifest record's photo list, understanding both the current
    "image_files" (list) shape and the original single-photo "image_file"
    shape, so pets registered before multi-photo support still load."""
    image_files = record.get("image_files")
    if image_files is not None:
        return list(image_files)
    legacy = record.get("image_file")
    return [legacy] if legacy else []


class PetProfileStore:
    def __init__(self, root=DEFAULT_PROFILE_DIR, max_pets=MAX_PETS):
        self.root = Path(root)
        self.images_dir = self.root / "images"
        self.manifest_path = self.root / "profiles.json"
        self.max_pets = int(max_pets)
        if self.max_pets < 1 or self.max_pets > MAX_PETS:
            raise ValueError(f"max_pets must be between 1 and {MAX_PETS}.")

    def _records(self):
        if not self.manifest_path.exists():
            return []
        try:
            payload = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ValueError(f"Pet profile manifest is invalid: {error}") from error
        if not isinstance(payload, dict) or not isinstance(payload.get("pets"), list):
            raise ValueError("Pet profile manifest must contain a 'pets' list.")
        if len(payload["pets"]) > self.max_pets:
            raise ValueError("Pet profile manifest exceeds the two-pet limit.")
        return payload["pets"]

    def _profile(self, record):
        if not isinstance(record, dict):
            raise ValueError("Each pet profile manifest entry must be an object.")
        profile_id = str(record.get("id", "")).strip()
        if not profile_id or not profile_id.replace("-", "").isalnum():
            raise ValueError("Pet profile id is invalid.")
        name = _clean_name(record.get("name"))

        image_files = _image_files(record)
        if not image_files:
            raise ValueError("Pet profile must have at least one reference image.")

        image_paths = []
        for image_file in image_files:
            image_file_path = Path(str(image_file))
            if image_file_path.is_absolute() or not image_file_path.parts:
                raise ValueError("Pet profile image path must be managed and relative.")
            image_path = (self.root / image_file_path).resolve()
            try:
                image_path.relative_to(self.images_dir.resolve())
            except ValueError as error:
                raise ValueError("Pet profile image escapes managed storage.") from error
            _validate_image(image_path)
            image_paths.append(image_path)

        return PetProfile(
            profile_id=profile_id,
            name=name,
            image_paths=tuple(image_paths),
            created_at=str(record.get("created_at", "")),
        )

    def list(self):
        return [self._profile(record) for record in self._records()]

    def _write_records(self, records):
        self.root.mkdir(parents=True, exist_ok=True)
        temporary = self.manifest_path.with_name(f".{self.manifest_path.name}.tmp")
        temporary.write_text(
            json.dumps({"version": 1, "pets": records}, indent=4, ensure_ascii=False),
            encoding="utf-8",
        )
        temporary.replace(self.manifest_path)

    def _store_image(self, profile_id, source, suffix_hint=""):
        """Copy a validated source image into managed storage and return
        its path relative to self.root, ready to go in a manifest record."""
        suffix = ".jpg" if source.suffix.lower() in {".jpg", ".jpeg"} else ".png"
        image_file = Path("images") / f"{profile_id}{suffix_hint}{suffix}"
        destination = self.root / image_file
        self.images_dir.mkdir(parents=True, exist_ok=True)
        temporary_image = destination.with_name(f".{destination.name}.tmp")
        shutil.copyfile(source, temporary_image)
        temporary_image.replace(destination)
        return image_file, destination

    def register(self, name, image_paths):
        """Register a new pet with one or more reference photos."""
        if isinstance(image_paths, (str, Path)):
            image_paths = [image_paths]
        image_paths = list(image_paths)
        if not image_paths:
            raise ValueError("At least one reference image is required.")

        clean_name = _clean_name(name)
        sources = [_validate_image(path) for path in image_paths]
        records = self._records()
        profiles = [self._profile(record) for record in records]
        if len(profiles) >= self.max_pets:
            raise ValueError(f"At most {self.max_pets} pet profiles can be registered.")
        if any(profile.name.casefold() == clean_name.casefold() for profile in profiles):
            raise ValueError(f"A pet named '{clean_name}' is already registered.")

        profile_id = uuid4().hex
        image_files = []
        copied_destinations = []
        try:
            for index, source in enumerate(sources):
                image_file, destination = self._store_image(profile_id, source, f"-{index}")
                copied_destinations.append(destination)
                image_files.append(image_file.as_posix())

            record = {
                "id": profile_id,
                "name": clean_name,
                "image_files": image_files,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            self._write_records(records + [record])
        except Exception:
            for destination in copied_destinations:
                destination.unlink(missing_ok=True)
            raise
        return self._profile(record)

    def _find_record_index(self, records, identifier):
        target = str(identifier or "").strip().casefold()
        return next(
            (
                index
                for index, record in enumerate(records)
                if str(record.get("id", "")).casefold() == target
                or str(record.get("name", "")).strip().casefold() == target
            ),
            None,
        )

    def add_image(self, identifier, image_path):
        """Append another reference photo to an already-registered pet."""
        records = self._records()
        match_index = self._find_record_index(records, identifier)
        if match_index is None:
            raise KeyError(f"No pet profile matches '{identifier}'.")

        record = records[match_index]
        source = _validate_image(image_path)
        existing_files = _image_files(record)

        image_file, destination = self._store_image(record["id"], source, f"-{uuid4().hex[:8]}")
        updated_record = {
            "id": record["id"],
            "name": record["name"],
            "image_files": existing_files + [image_file.as_posix()],
            "created_at": record.get("created_at", ""),
        }
        try:
            records[match_index] = updated_record
            self._write_records(records)
        except Exception:
            destination.unlink(missing_ok=True)
            raise
        return self._profile(updated_record)

    def remove(self, identifier):
        records = self._records()
        match_index = self._find_record_index(records, identifier)
        if match_index is None:
            raise KeyError(f"No pet profile matches '{identifier}'.")

        removed = self._profile(records[match_index])
        self._write_records(
            [record for index, record in enumerate(records) if index != match_index]
        )
        for image_path in removed.image_paths:
            image_path.unlink(missing_ok=True)
        return removed


def register_pet_profile(name, image_paths, profile_dir=DEFAULT_PROFILE_DIR):
    return PetProfileStore(profile_dir).register(name, image_paths)


def add_pet_image(identifier, image_path, profile_dir=DEFAULT_PROFILE_DIR):
    return PetProfileStore(profile_dir).add_image(identifier, image_path)


def list_pet_profiles(profile_dir=DEFAULT_PROFILE_DIR):
    return PetProfileStore(profile_dir).list()


def remove_pet_profile(identifier, profile_dir=DEFAULT_PROFILE_DIR):
    return PetProfileStore(profile_dir).remove(identifier)
