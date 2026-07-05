class CandidateFrameQueue:
    """
    Turns a raw per-sample motion signal into a bounded stream of candidate
    frames: one immediately when motion starts, then at most one per
    cooldown window for as long as that motion burst continues. This is
    what controls vision-model call volume downstream, not the raw
    motion-flagged frame count.
    """

    def __init__(self, detector, cooldown_sec=4.0):
        self.detector = detector
        self.cooldown_sec = cooldown_sec
        self.is_moving = False
        self.last_candidate_ts = None

    def observe(self, frame, small_frame, timestamp, frame_index):
        """
        :param frame: full-res frame, stored on the candidate for the
            vision model stage (never itself fed to the detector).
        :param small_frame: downscaled frame, fed to the detector.
        :return: a candidate dict, or None if this sample isn't a candidate.
        """
        result = self.detector.detect(small_frame)

        candidate = None

        if result["motion"]:
            just_started = not self.is_moving
            cooldown_elapsed = (
                self.last_candidate_ts is None
                or (timestamp - self.last_candidate_ts) >= self.cooldown_sec
            )
            if just_started or cooldown_elapsed:
                candidate = {
                    "frame_index": frame_index,
                    "timestamp": timestamp,
                    "changed_area": result["changed_area"],
                    "num_contours": result["num_contours"],
                    "frame": frame,
                }
                self.last_candidate_ts = timestamp
            self.is_moving = True
        else:
            # burst ended: next burst's first candidate should fire
            # immediately, not wait out a cooldown from the previous one
            self.is_moving = False
            self.last_candidate_ts = None

        return candidate
