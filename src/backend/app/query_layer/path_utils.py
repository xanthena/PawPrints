"""Stable repository-relative paths for API response JSON."""

import os
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]


def relative_repo_path(path, repo_root=REPO_ROOT):
    """Return a forward-slash path relative to the repository root."""
    if path is None:
        return None
    relative = os.path.relpath(Path(path).resolve(), Path(repo_root).resolve())
    return Path(relative).as_posix()

