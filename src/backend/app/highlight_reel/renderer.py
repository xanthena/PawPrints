import shutil
import subprocess
import tempfile
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
            "FFmpeg was not found. Install highlight_reel/requirements.txt "
            "or pass --ffmpeg."
        ) from error


def _run(command, description):
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        details = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"FFmpeg failed while {description}:\n{details}")


def _concat_entry(path):
    escaped_path = path.as_posix().replace("'", "'\\''")
    return f"file '{escaped_path}'\n"


def render_highlight_reel(video_path, clips, output_path, ffmpeg_path=None):
    """Cut selected clips, normalize their streams, and concatenate an MP4."""
    source = Path(video_path).resolve()
    destination = Path(output_path).resolve()
    if not source.is_file():
        raise FileNotFoundError(f"Source video does not exist: {source}")
    if not clips:
        raise ValueError("At least one highlight clip is required.")

    destination.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg = resolve_ffmpeg(ffmpeg_path)

    with tempfile.TemporaryDirectory(
        prefix="highlight-reel-",
        dir=destination.parent,
    ) as temporary_directory:
        temporary = Path(temporary_directory)
        segment_paths = []

        for index, clip in enumerate(clips, start=1):
            segment = temporary / f"segment_{index:03d}.mp4"
            command = [
                ffmpeg,
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-ss",
                f"{clip.clip_start:.3f}",
                "-t",
                f"{clip.duration:.3f}",
                "-i",
                str(source),
                "-map",
                "0:v:0",
                "-map",
                "0:a?",
                "-c:v",
                "libx264",
                "-preset",
                "fast",
                "-crf",
                "21",
                "-c:a",
                "aac",
                "-b:a",
                "160k",
                "-avoid_negative_ts",
                "make_zero",
                "-movflags",
                "+faststart",
                str(segment),
            ]
            _run(command, f"creating segment {index}")
            segment_paths.append(segment)

        concat_file = temporary / "segments.txt"
        concat_file.write_text(
            "".join(_concat_entry(path) for path in segment_paths),
            encoding="utf-8",
        )
        rendered = temporary / "highlight_reel.mp4"
        _run(
            [
                ffmpeg,
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_file),
                "-c",
                "copy",
                "-movflags",
                "+faststart",
                str(rendered),
            ],
            "joining selected clips",
        )
        rendered.replace(destination)

    return destination

