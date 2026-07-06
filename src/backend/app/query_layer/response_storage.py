"""Dated, collision-safe storage for query response JSON files."""

import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4


REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_RESPONSE_ROOT = REPO_ROOT / "src" / "results" / "query-results"


def _local_now(now=None):
    if now is None:
        return datetime.now().astimezone()
    return now.astimezone() if now.tzinfo is not None else now.astimezone()


def daily_response_dir(
    include_proof,
    response_root=DEFAULT_RESPONSE_ROOT,
    now=None,
):
    """Separate proof and non-proof responses inside today's folder."""
    current = _local_now(now)
    category = "proof_requested" if include_proof else "proof_not_requested"
    return Path(response_root) / current.date().isoformat() / category


def store_query_response(
    response,
    include_proof,
    response_root=DEFAULT_RESPONSE_ROOT,
    now=None,
    response_id=None,
):
    """Atomically save one response without overwriting an earlier query."""
    destination = daily_response_dir(include_proof, response_root, now)
    destination.mkdir(parents=True, exist_ok=True)

    identifier = response_id or uuid4().hex
    if not identifier.replace("-", "").isalnum():
        raise ValueError("response_id may contain only letters, numbers, and hyphens.")

    candidate = destination / f"{identifier}_query_response.json"
    while candidate.exists():
        identifier = uuid4().hex
        candidate = destination / f"{identifier}_query_response.json"

    temporary = candidate.with_name(f".{candidate.name}.tmp")
    temporary.write_text(
        json.dumps(response, indent=4, ensure_ascii=False),
        encoding="utf-8",
    )
    temporary.replace(candidate)
    return candidate.resolve()

