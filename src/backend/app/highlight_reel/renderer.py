import tempfile
import textwrap
from pathlib import Path

from app.media_tools import concat_file_entry, resolve_ffmpeg, run_ffmpeg


FONT_CANDIDATES = (
    # Prefer plain upright sans-serif faces on each supported platform.
    Path("C:/Windows/Fonts/arial.ttf"),
    Path("C:/Windows/Fonts/segoeui.ttf"),
    Path("/System/Library/Fonts/HelveticaNeue.ttc"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
)


def resolve_caption_font(font_path=None):
    if font_path:
        font = Path(font_path).expanduser().resolve()
        if not font.is_file():
            raise FileNotFoundError(f"Caption font does not exist: {font}")
        return font
    return next((path for path in FONT_CANDIDATES if path.is_file()), None)


def _escape_filter_path(path):
    value = Path(path).resolve().as_posix()
    return value.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")


def _wrapped_caption(value, width=42):
    normalized = " ".join(str(value or "").split())
    lines = textwrap.wrap(
        normalized,
        width=max(width - 2, 1),
        max_lines=2,
        placeholder="...",
    )
    if not lines:
        return "[]"
    lines[0] = f"[{lines[0]}"
    lines[-1] = f"{lines[-1]}]"
    return "\n".join(lines)


def build_caption_filter(caption_file, font_path=None):
    """Build a warm-yellow, classic film-subtitle drawtext filter."""
    options = []
    font = resolve_caption_font(font_path)
    if font:
        options.append(f"fontfile='{_escape_filter_path(font)}'")
    options.extend(
        [
            f"textfile='{_escape_filter_path(caption_file)}'",
            "reload=0",
            "expansion=none",
            "fontcolor=white",
            "fontsize=h/26",
            "line_spacing=2",
            "text_align=C",
            "x=(w-text_w)/2",
            "y=h-text_h-h*0.045",
            "box=1",
            "boxcolor=black@0.24",
            "boxborderw=5",
        ]
    )
    return f"drawtext={':'.join(options)}"


def render_highlight_reel(
    video_path,
    clips,
    output_path,
    ffmpeg_path=None,
    caption_font_path=None,
):
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
            caption_file = temporary / f"caption_{index:03d}.txt"
            caption_file.write_text(
                _wrapped_caption(clip.caption),
                encoding="utf-8",
                newline="\n",
            )
            video_filter = build_caption_filter(caption_file, caption_font_path)
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
                "-vf",
                video_filter,
                "-preset",
                "fast",
                "-crf",
                "21",
                "-c:a",
                "aac",
                "-pix_fmt",
                "yuv420p",
                "-b:a",
                "160k",
                "-avoid_negative_ts",
                "make_zero",
                "-movflags",
                "+faststart",
                str(segment),
            ]
            run_ffmpeg(command, f"creating segment {index}")
            segment_paths.append(segment)

        concat_file = temporary / "segments.txt"
        concat_file.write_text(
            "".join(concat_file_entry(path) for path in segment_paths),
            encoding="utf-8",
        )
        rendered = temporary / "highlight_reel.mp4"
        run_ffmpeg(
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

