"""Typed records shared by the query layer."""

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path


@dataclass(frozen=True)
class DateScope:
    start_date: date
    end_date: date


@dataclass(frozen=True)
class QueryIntent:
    original_question: str
    answer_type: str
    activities: tuple[str, ...] = ()
    objects: tuple[str, ...] = ()
    relation: str | None = None

    @property
    def supported(self):
        return bool(self.activities or self.objects)

    @property
    def target_label(self):
        if self.activities:
            return self.activities[0].replace("_", " ")
        if self.objects:
            return f"activity involving {self.objects[0].replace('_', ' ')}"
        return "requested activity"


@dataclass(frozen=True)
class TimelineEvent:
    event_date: date
    source_json: Path
    source_video: Path | None
    source_video_error: str | None
    data: dict

    @property
    def activity(self):
        return str(self.data.get("activity", "unknown"))

    @property
    def start_time(self):
        return float(self.data.get("start_time", 0.0))

    @property
    def end_time(self):
        return float(self.data.get("end_time", self.start_time))

    @property
    def duration(self):
        return max(0.0, float(self.data.get("duration", self.end_time - self.start_time)))

    @property
    def clip_start(self):
        return max(0.0, float(self.data.get("clip_start", self.start_time)))

    @property
    def clip_end(self):
        return max(self.clip_start, float(self.data.get("clip_end", self.end_time)))


@dataclass(frozen=True)
class QueryMatch:
    event: TimelineEvent
    score: float
    reasons: tuple[str, ...]


@dataclass
class RepositoryResult:
    events: list[TimelineEvent] = field(default_factory=list)
    timeline_files: list[Path] = field(default_factory=list)
    available_dates: list[date] = field(default_factory=list)
    missing_dates: list[date] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ProofSegment:
    event_date: date
    source_video: Path
    clip_start: float
    clip_end: float
    evidence_indices: tuple[int, ...]

    @property
    def duration(self):
        return self.clip_end - self.clip_start

