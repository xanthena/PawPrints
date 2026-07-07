class CandidateFrameQueue:
    """
    Turns a raw per-sample motion signal into a bounded stream of events:
    a "candidate" the instant a motion burst starts, at most one more per
    cooldown window for as long as it continues, a single free "burst_end"
    marker (no frame, no vision-model cost) the moment it stops, and --
    while still -- one coarse "still_ping" candidate per still_ping_interval_sec.

    Without the still ping, a cat settling in to sleep would only ever be
    captured once, at the moment it went still; nothing would tell the
    vision model to check in again until it wakes up or something else in
    the scene moves. The still ping is what turns that silence into actual
    "still sleeping" events instead of an unlabeled gap.
    """

    def __init__(self, detector, cooldown_sec=4.0, still_ping_interval_sec=10.0):
        self.detector = detector
        self.cooldown_sec = cooldown_sec
        self.still_ping_interval_sec = still_ping_interval_sec
        self.is_moving = False
        self.last_candidate_ts = None
        self.last_still_ping_ts = None

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
            self.last_still_ping_ts = None  # next stillness gets its own fresh clock

            if just_started or cooldown_elapsed:
                self.last_candidate_ts = timestamp
                return {
                    "kind": "candidate",
                    "trigger": "motion",
                    "frame_index": frame_index,
                    "timestamp": timestamp,
                    "changed_area": result["changed_area"],
                    "num_contours": result["num_contours"],
                    "frame": frame,
                }
            return None

        if self.is_moving:
            # first still sample right after a burst: fire the end marker
            # exactly once, and start the still-ping clock from here
            self.is_moving = False
            self.last_candidate_ts = None
            self.last_still_ping_ts = timestamp
            return {
                "kind": "burst_end",
                "frame_index": frame_index,
                "timestamp": timestamp,
            }

        # already still: check in periodically so long stillness (sleeping)
        # still produces real events instead of a silent gap. last_still_ping_ts
        # being None here means we've been still since before observe() was
        # ever called (e.g. the feed starts on an already-sleeping cat), so
        # ping immediately rather than waiting out a full interval blind.
        if self.still_ping_interval_sec is not None and (
            self.last_still_ping_ts is None
            or (timestamp - self.last_still_ping_ts) >= self.still_ping_interval_sec
        ):
            self.last_still_ping_ts = timestamp
            return {
                "kind": "candidate",
                "trigger": "still_ping",
                "frame_index": frame_index,
                "timestamp": timestamp,
                "changed_area": result["changed_area"],
                "num_contours": result["num_contours"],
                "frame": frame,
            }

        return None
