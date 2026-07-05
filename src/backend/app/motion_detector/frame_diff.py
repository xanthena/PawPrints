import cv2 as cv

from .base import MotionDetector


class FrameDiffDetector(MotionDetector):
    """Detects motion by comparing each frame against the previous one."""

    def __init__(self, use_contours=False, min_area_frac=0.005, diff_threshold=25):
        super().__init__(use_contours, min_area_frac)
        self.diff_threshold = diff_threshold
        self.prev_gray = None

    def detect(self, frame) -> dict:
        gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
        gray = cv.GaussianBlur(gray, (21, 21), 0)

        if self.prev_gray is None:
            self.prev_gray = gray
            return {"motion": False, "changed_area": 0, "num_contours": None}

        diff = cv.absdiff(self.prev_gray, gray)
        _, mask = cv.threshold(diff, self.diff_threshold, 255, cv.THRESH_BINARY)

        self.prev_gray = gray

        return self._decide(mask)
