"""Managed temporary storage and expiration for query proof videos."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4


REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_PROOF_ROOT = REPO_ROOT / "src" / "results" / "query-proofs" / "temp"


@dataclass(frozen=True)
class ProofArtifact:
    query_id: str
    output_dir: Path
    expires_at: datetime


def _local_now(now=None):
    if now is None:
        return datetime.now().astimezone()
    if now.tzinfo is None:
        return now.astimezone()
    return now


def create_proof_artifact(
    proof_root=DEFAULT_PROOF_ROOT,
    ttl_hours=24,
    now=None,
    query_id=None,
):
    """Create a unique dated output directory for one query's proof clips."""
    if ttl_hours <= 0:
        raise ValueError("ttl_hours must be greater than 0.")

    current = _local_now(now)
    identifier = query_id or uuid4().hex
    if not identifier.replace("-", "").isalnum():
        raise ValueError("query_id may contain only letters, numbers, and hyphens.")

    output_dir = Path(proof_root) / current.date().isoformat()
    output_dir.mkdir(parents=True, exist_ok=True)
    return ProofArtifact(
        query_id=identifier,
        output_dir=output_dir.resolve(),
        expires_at=current + timedelta(hours=ttl_hours),
    )


def cleanup_expired_proofs(proof_root=DEFAULT_PROOF_ROOT, max_age_hours=24, now=None):
    """Delete expired managed proof MP4s and return their paths."""
    if max_age_hours <= 0:
        raise ValueError("max_age_hours must be greater than 0.")

    root = Path(proof_root)
    if not root.is_dir():
        return []

    cutoff = _local_now(now).timestamp() - (max_age_hours * 3600)
    deleted = []
    # Matches both the legacy single-stitched-video name ("..._query_proof.mp4")
    # and the current per-segment names ("..._query_proof_1.mp4", "..._query_proof_2.mp4", ...).
    for path in root.rglob("*_query_proof*.mp4"):
        if path.is_file() and path.stat().st_mtime < cutoff:
            path.unlink()
            deleted.append(path)

    for directory in sorted(
        (path for path in root.rglob("*") if path.is_dir()),
        key=lambda path: len(path.parts),
        reverse=True,
    ):
        try:
            directory.rmdir()
        except OSError:
            pass
    return deleted

