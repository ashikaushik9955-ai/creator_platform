import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

PROFILES = {
    "low":    {"width": 640,  "crf": 28, "audio_bitrate": "96k"},
    "medium": {"width": 1280, "crf": 23, "audio_bitrate": "128k"},
    "high":   {"width": 1920, "crf": 18, "audio_bitrate": "192k"},
}

QUALITIES = tuple(PROFILES)

FFMPEG_TIMEOUT_SECONDS = 30 * 60  # 30 मिनट


class VideoProcessingError(Exception):
    """Raised when FFmpeg fails or times out."""


def generate_video_version(
    input_path: Path,
    output_path: Path,
    quality: str,
    timeout: int = FFMPEG_TIMEOUT_SECONDS,
) -> Path:
    """Generate one quality version of a video using FFmpeg."""

    if quality not in PROFILES:
        raise ValueError(f"Unsupported quality: {quality}")

    profile = PROFILES[quality]

    command = [
        "ffmpeg",
        "-nostdin",
        "-loglevel", "error",
        "-y",
        "-i", str(input_path),
        "-vf", f"scale='min({profile['width']},iw)':-2",
        "-c:v", "libx264",
        "-crf", str(profile["crf"]),
        "-preset", "medium",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", profile["audio_bitrate"],
        "-movflags", "+faststart",
        str(output_path),
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        output_path.unlink(missing_ok=True)
        logger.error("FFmpeg timed out after %ss (%s)", timeout, quality)
        raise VideoProcessingError(f"FFmpeg timed out ({quality})")

    if result.returncode != 0:
        output_path.unlink(missing_ok=True)
        logger.error("FFmpeg failed (%s): %s", quality, result.stderr[-4000:])
        raise VideoProcessingError(
            f"FFmpeg failed ({quality}), exit code {result.returncode}"
        )

    return output_path