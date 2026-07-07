import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
from PIL import Image


BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.vision_model import identity_matcher


PNG_BYTES = b"\x89PNG\r\n\x1a\n" + (b"identity-image" * 4)


class _FakeProfile:
    def __init__(self, name, image_paths):
        self.name = name
        self.image_paths = tuple(image_paths)


def _touch(path):
    path.write_bytes(PNG_BYTES)
    return path


class IdentityMatcherTests(unittest.TestCase):
    def setUp(self):
        identity_matcher._embedding_cache.clear()

    def _fake_embed(self, vectors_by_name):
        """Returns an embed_image replacement that looks up a fixed vector
        by filename stem instead of running real CLIP inference."""

        def _embed(path):
            return np.array(vectors_by_name[Path(path).stem], dtype=float)

        return _embed

    def test_same_image_scores_maximum_similarity(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate = _touch(root / "candidate.png")
            milo_photo = _touch(root / "milo.png")
            profile = _FakeProfile("Milo", [milo_photo])

            vector = [1.0, 0.0, 0.0]
            with patch.object(
                identity_matcher,
                "embed_image",
                self._fake_embed({"candidate": vector, "milo": vector}),
            ):
                matches = identity_matcher.match_identity(candidate, [profile])

        self.assertEqual(matches, ["Milo"])

    def test_visually_distinct_images_do_not_match(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate = _touch(root / "candidate.png")
            milo_photo = _touch(root / "milo.png")
            profile = _FakeProfile("Milo", [milo_photo])

            with patch.object(
                identity_matcher,
                "embed_image",
                self._fake_embed(
                    {"candidate": [1.0, 0.0, 0.0], "milo": [0.0, 1.0, 0.0]}
                ),
            ):
                matches = identity_matcher.match_identity(candidate, [profile])

        self.assertEqual(matches, [])

    def test_no_registered_profiles_returns_empty_list(self):
        with tempfile.TemporaryDirectory() as directory:
            candidate = _touch(Path(directory) / "candidate.png")
            with patch.object(
                identity_matcher, "embed_image", self._fake_embed({"candidate": [1.0, 0.0]})
            ):
                matches = identity_matcher.match_identity(candidate, [])

        self.assertEqual(matches, [])

    def test_uses_best_matching_photo_among_several(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate = _touch(root / "candidate.png")
            far_photo = _touch(root / "milo_far.png")
            close_photo = _touch(root / "milo_close.png")
            profile = _FakeProfile("Milo", [far_photo, close_photo])

            with patch.object(
                identity_matcher,
                "embed_image",
                self._fake_embed(
                    {
                        "candidate": [1.0, 0.0],
                        "milo_far": [0.0, 1.0],
                        "milo_close": [1.0, 0.0],
                    }
                ),
            ):
                matches = identity_matcher.match_identity(candidate, [profile])

        self.assertEqual(matches, ["Milo"])

    def test_cached_embedding_only_computes_once_per_path(self):
        with tempfile.TemporaryDirectory() as directory:
            photo = _touch(Path(directory) / "milo.png")
            calls = []

            def _embed(path):
                calls.append(path)
                return np.array([1.0, 0.0])

            with patch.object(identity_matcher, "embed_image", _embed):
                identity_matcher._cached_embedding(photo)
                identity_matcher._cached_embedding(photo)

        self.assertEqual(len(calls), 1)


class _FakeBox:
    def __init__(self, cls_id, confidence, xyxy):
        self.cls = [cls_id]
        self.conf = [confidence]
        self.xyxy = [np.array(xyxy, dtype=float)]


class _FakeDetectionResult:
    def __init__(self, boxes, names):
        self.boxes = boxes
        self.names = names


def _fake_detector(boxes, names=None):
    """A stand-in for the real YOLO callable -- avoids running real
    detector inference in the fast test suite."""
    detector = MagicMock()
    detector.return_value = [_FakeDetectionResult(boxes, names or {0: "cat"})]
    return detector


class CatDetectionTests(unittest.TestCase):
    def test_detect_cat_box_pads_and_clamps_to_image_bounds(self):
        # 100x100 box inside a 250x250 image, padded 15% each side --
        # comfortably within bounds, so clamping shouldn't kick in.
        boxes = [_FakeBox(0, 0.9, [100, 100, 200, 200])]
        with patch.object(
            identity_matcher, "_get_detector", return_value=_fake_detector(boxes)
        ):
            box = identity_matcher._detect_cat_box("unused.jpg", (250, 250))

        self.assertEqual(box, (85.0, 85.0, 215.0, 215.0))

    def test_detect_cat_box_clamps_padding_to_image_edge(self):
        # Box already touches the top-left corner -- padding must not
        # push the crop into negative coordinates.
        boxes = [_FakeBox(0, 0.9, [0, 0, 100, 100])]
        with patch.object(
            identity_matcher, "_get_detector", return_value=_fake_detector(boxes)
        ):
            box = identity_matcher._detect_cat_box("unused.jpg", (250, 250))

        self.assertEqual(box[0], 0)
        self.assertEqual(box[1], 0)

    def test_detect_cat_box_returns_none_without_a_cat_class(self):
        boxes = [_FakeBox(1, 0.95, [0, 0, 100, 100])]  # class 1 = "dog"
        with patch.object(
            identity_matcher,
            "_get_detector",
            return_value=_fake_detector(boxes, names={0: "cat", 1: "dog"}),
        ):
            box = identity_matcher._detect_cat_box("unused.jpg", (250, 250))

        self.assertIsNone(box)

    def test_detect_cat_box_picks_highest_confidence_cat(self):
        boxes = [
            _FakeBox(0, 0.4, [0, 0, 50, 50]),
            _FakeBox(0, 0.9, [100, 100, 200, 200]),
        ]
        with patch.object(
            identity_matcher, "_get_detector", return_value=_fake_detector(boxes)
        ):
            box = identity_matcher._detect_cat_box("unused.jpg", (250, 250))

        # The higher-confidence box is the padded (100,100,200,200) one,
        # not the lower-confidence (0,0,50,50) one.
        self.assertEqual(box, (85.0, 85.0, 215.0, 215.0))


class EmbedImageCroppingTests(unittest.TestCase):
    def _patch_model(self, captured):
        import torch

        def fake_preprocess(image):
            captured["size"] = image.size
            return torch.zeros(3, 224, 224)

        fake_model = MagicMock()
        fake_model.encode_image.return_value = torch.ones(1, 512)
        return patch.object(
            identity_matcher, "_get_model", return_value=(fake_model, fake_preprocess)
        )

    def test_embed_image_crops_to_the_detected_box(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "candidate.jpg"
            Image.new("RGB", (200, 100), color=(10, 20, 30)).save(path)

            captured = {}
            with self._patch_model(captured), patch.object(
                identity_matcher, "_detect_cat_box", return_value=(50, 20, 150, 80)
            ):
                identity_matcher.embed_image(path)

        self.assertEqual(captured["size"], (100, 60))

    def test_embed_image_falls_back_to_full_frame_without_a_detection(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "candidate.jpg"
            Image.new("RGB", (200, 100), color=(10, 20, 30)).save(path)

            captured = {}
            with self._patch_model(captured), patch.object(
                identity_matcher, "_detect_cat_box", return_value=None
            ):
                identity_matcher.embed_image(path)

        self.assertEqual(captured["size"], (200, 100))


if __name__ == "__main__":
    unittest.main()
