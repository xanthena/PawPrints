"""Shared safe FFmpeg discovery, execution, and concat-file helpers."""

import shutil
import subprocess
from pathlib import Path


def resolve_ffmpeg(ffmpeg_path=None):
    """Find FFmpeg from an explicit path, PATH, or imageio-ffmpeg."""
    if ffmpeg_path:
        executable = Path(ffmpeg_path).expanduser()
        if executable.is_file():
            return str(executable.resolve())
        raise FileNotFoundError(f"FFmpeg executable does not exist: {executable}")

    executable = shutil.which("ffmpeg")
    if executable:
        return executable

    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except (ImportError, RuntimeError) as error:
        raise RuntimeError(
            "FFmpeg was not found. Install the backend requirements or pass --ffmpeg."
        ) from error


def run_ffmpeg(command, description):
    """Run one argument-list command and raise an actionable rendering error."""
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        details = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"FFmpeg failed while {description}:\n{details}")


def concat_file_entry(path):
    """Return one safely quoted line for FFmpeg's concat demuxer."""
    escaped_path = Path(path).as_posix().replace("'", "'\\''")
    return f"file '{escaped_path}'\n"
