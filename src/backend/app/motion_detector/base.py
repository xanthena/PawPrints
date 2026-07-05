import cv2 as cv


class MotionDetector:
    """Base class for motion detection algorithms."""

    def __init__(self, use_contours=False, min_area_frac=0.005):
        self.use_contours = use_contours
        # fraction of frame area, not an absolute pixel count, so full-res
        # and downscaled instances can share the same constructor args
        self.min_area_frac = min_area_frac

    def _decide(self, mask):
        h, w = mask.shape[:2]
        min_area = self.min_area_frac * h * w

        if self.use_contours:
            contours, _ = cv.findContours(mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
            big = [c for c in contours if cv.contourArea(c) >= min_area]
            return {
                "motion": len(big) > 0,
                "changed_area": int(sum(cv.contourArea(c) for c in big)),
                "num_contours": len(big),
            }

        area = cv.countNonZero(mask)
        return {
            "motion": area > min_area,
            "changed_area": area,
            "num_contours": None,
        }
