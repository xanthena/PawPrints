import json
import sys
import tempfile
import unittest
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.pet_profiles import PetProfileStore


PNG_BYTES = b"\x89PNG\r\n\x1a\n" + (b"test-image" * 4)


class PetProfileStoreTests(unittest.TestCase):
    def test_registers_lists_and_removes_managed_reference(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            upload = root / "upload.png"
            upload.write_bytes(PNG_BYTES)
            store = PetProfileStore(root / "profiles")

            registered = store.register("  Milo  ", upload)
            listed = store.list()

            self.assertEqual(registered.name, "Milo")
            self.assertEqual([item.name for item in listed], ["Milo"])
            self.assertTrue(registered.image_path.is_file())
            self.assertNotEqual(registered.image_path, upload)
            manifest = json.loads(store.manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["pets"][0]["name"], "Milo")
            self.assertFalse(Path(manifest["pets"][0]["image_files"][0]).is_absolute())

            removed = store.remove("milo")

            self.assertEqual(removed.profile_id, registered.profile_id)
            self.assertEqual(store.list(), [])
            self.assertFalse(removed.image_path.exists())

    def test_registers_with_multiple_images_and_can_add_more_later(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            store = PetProfileStore(root / "profiles")
            first = root / "one.png"
            first.write_bytes(PNG_BYTES)
            second = root / "two.png"
            second.write_bytes(PNG_BYTES)

            registered = store.register("Milo", [first, second])
            self.assertEqual(len(registered.image_paths), 2)
            self.assertTrue(all(path.is_file() for path in registered.image_paths))

            third = root / "three.png"
            third.write_bytes(PNG_BYTES)
            updated = store.add_image("Milo", third)
            self.assertEqual(len(updated.image_paths), 3)

            listed = store.list()
            self.assertEqual(len(listed[0].image_paths), 3)

            removed = store.remove("Milo")
            self.assertEqual(len(removed.image_paths), 3)
            self.assertFalse(any(path.exists() for path in removed.image_paths))

    def test_renames_pet_keeping_id_and_photos(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            store = PetProfileStore(root / "profiles")
            upload = root / "upload.png"
            upload.write_bytes(PNG_BYTES)

            registered = store.register("Milo", upload)
            renamed = store.rename("milo", "  Oscar  ")

            self.assertEqual(renamed.name, "Oscar")
            self.assertEqual(renamed.profile_id, registered.profile_id)
            self.assertEqual(renamed.image_paths, registered.image_paths)
            self.assertEqual([item.name for item in store.list()], ["Oscar"])

    def test_rename_rejects_collision_with_other_pet(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            store = PetProfileStore(root / "profiles")
            first = root / "first.png"
            first.write_bytes(PNG_BYTES)
            second = root / "second.png"
            second.write_bytes(PNG_BYTES)
            store.register("Milo", first)
            store.register("Luna", second)

            with self.assertRaisesRegex(ValueError, "already registered"):
                store.rename("Luna", "milo")

    def test_rename_missing_pet_raises_key_error(self):
        with tempfile.TemporaryDirectory() as directory:
            store = PetProfileStore(Path(directory) / "profiles")
            with self.assertRaises(KeyError):
                store.rename("nobody", "New Name")

    def test_enforces_two_pet_limit_and_unique_names(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            store = PetProfileStore(root / "profiles")
            uploads = []
            for index in range(3):
                upload = root / f"upload-{index}.png"
                upload.write_bytes(PNG_BYTES)
                uploads.append(upload)

            store.register("Milo", uploads[0])
            with self.assertRaisesRegex(ValueError, "already registered"):
                store.register("mILO", uploads[1])
            store.register("Luna", uploads[1])
            with self.assertRaisesRegex(ValueError, "At most 2"):
                store.register("Nova", uploads[2])

    def test_rejects_extension_content_mismatch(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            upload = root / "fake.png"
            upload.write_bytes(b"not an image")
            store = PetProfileStore(root / "profiles")

            with self.assertRaisesRegex(ValueError, "content"):
                store.register("Milo", upload)

    def test_rejects_manifest_path_escape(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile_root = root / "profiles"
            profile_root.mkdir()
            outside = root / "outside.png"
            outside.write_bytes(PNG_BYTES)
            (profile_root / "profiles.json").write_text(
                json.dumps(
                    {
                        "version": 1,
                        "pets": [
                            {
                                "id": "safeid",
                                "name": "Milo",
                                "image_file": "../outside.png",
                                "created_at": "now",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "escapes"):
                PetProfileStore(profile_root).list()


if __name__ == "__main__":
    unittest.main()
