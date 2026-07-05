class CandidateFrameQueue:
    """
    Turns a raw per-sample motion signal into a bounded stream of events:
    a "candidate" the instant a motion burst starts, at most one more per
    cooldown window for as long as it continues, and a single free
    "burst_end" marker (no frame, no vision-model cost) the moment it
    stops -- so the Event Builder can compute a duration without an extra
    API call.
    """

    def __init__(self, detector, cooldown_sec=4.0):
        self.detector = detector
        self.cooldown_sec = cooldown_sec
        self.is_moving = False
        self.last_candidate_ts = None

    def observe(self, frame, small_frame, timestamp, frame_index):
        """
        :param frame: full-res frame, stored on candidate events for the
            vision model stage (never itself fed to the detector).
        :param small_frame: downscaled frame, fed to the detector.
        :return: an event dict, or None if this sample isn't one.
        """
        result = self.detector.detect(small_frame)

        if result["motion"]:
            just_started = not self.is_moving
            cooldown_elapsed = (
                self.last_candidate_ts is None
                or (timestamp - self.last_candidate_ts) >= self.cooldown_sec
            )
            self.is_moving = True

            if just_started or cooldown_elapsed:
                self.last_candidate_ts = timestamp
                return {
                    "kind": "candidate",
                    "frame_index": frame_index,
                    "timestamp": timestamp,
                    "changed_area": result["changed_area"],
                    "num_contours": result["num_contours"],
                    "frame": frame,
                }
            return None

        if self.is_moving:
            # first still sample right after a burst: fire the end marker
            # exactly once, then go quiet until the next burst starts
            self.is_moving = False
            self.last_candidate_ts = None
            return {
                "kind": "burst_end",
                "frame_index": frame_index,
                "timestamp": timestamp,
            }

        return None
