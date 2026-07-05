import cv2 as cv

from .base import MotionDetector


class MOG2Detector(MotionDetector):
    """Detects motion via MOG2 background subtraction."""

    def __init__(self, use_contours=False, min_area_frac=0.005):
        super().__init__(use_contours, min_area_frac)
        self.subtractor = cv.createBackgroundSubtractorMOG2(detectShadows=True)

    def detect(self, frame) -> dict:
        fg = self.subtractor.apply(frame)
        # drop the shadow value (127); only the full-strength foreground (255) counts
        _, mask = cv.threshold(fg, 200, 255, cv.THRESH_BINARY)
        return self._decide(mask)
