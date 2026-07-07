"""Managed names and reference photos for up to two household cats."""

from .store import (
    DEFAULT_PROFILE_DIR,
    MAX_PETS,
    PetProfile,
    PetProfileStore,
    add_pet_image,
    list_pet_profiles,
    register_pet_profile,
    remove_pet_profile,
    rename_pet_profile,
)

__all__ = [
    "DEFAULT_PROFILE_DIR",
    "MAX_PETS",
    "PetProfile",
    "PetProfileStore",
    "add_pet_image",
    "list_pet_profiles",
    "register_pet_profile",
    "remove_pet_profile",
    "rename_pet_profile",
]
