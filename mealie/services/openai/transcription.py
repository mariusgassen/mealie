import functools
import re
from pathlib import Path
from typing import TypedDict

from mealie.core import exceptions
from mealie.core.config import get_app_settings
from mealie.core.root_logger import get_logger

SUBTITLE_LANGS = ["en", "fr", "es", "de", "it"]

logger = get_logger()


class TranscribedAudio(TypedDict):
    subtitle: Path | None
    title: str
    description: str
    thumbnail_url: str | None


@functools.cache
def get_yt_dlp_extractors() -> list:
    """Build and cache the yt-dlp extractor list once per process lifetime."""
    import yt_dlp
    from yt_dlp.extractor.generic import GenericIE

    return [ie for ie in yt_dlp.extractor.gen_extractors() if ie.working() and not isinstance(ie, GenericIE)]


def is_video_url(url: str) -> bool:
    """Whether yt-dlp recognizes the URL as something it can download."""

    if not url:
        return False

    return any(ie.suitable(url) for ie in get_yt_dlp_extractors())


def parse_subtitle_content(subtitle_content: str) -> str:
    # TODO: is there a better way to parse subtitles that's more efficient?

    lines = []
    for line in subtitle_content.split("\n"):
        if line.strip() and not line.startswith("WEBVTT") and "-->" not in line and not line.isdigit():
            lines.append(line.strip())

    raw_content = " ".join(lines)
    content = re.sub(r"<[^>]+>", "", raw_content)
    return content


def download_video(url: str, temp_path: Path) -> TranscribedAudio:
    """Downloads a video's metadata and subtitles. The audio/video itself is never downloaded:
    Mealie doesn't transcribe it with AI, so there's nothing to do with the media file."""

    import yt_dlp

    output_template = temp_path / "mealie"  # No extension here

    ydl_opts = {
        "outtmpl": str(output_template) + ".%(ext)s",
        "quiet": True,
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitleslangs": SUBTITLE_LANGS,
        "skip_download": True,
        "ignoreerrors": True,
    }

    settings = get_app_settings()
    if settings.YTDLP_COOKIEFILE:
        ydl_opts["cookiefile"] = settings.YTDLP_COOKIEFILE

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

            if info is None:
                raise exceptions.VideoDownloadError(
                    "Failed to extract video information. The video may be unavailable or the URL is invalid."
                )

            sub_path = None
            for lang in SUBTITLE_LANGS:
                potential_path = output_template.with_suffix(f".{lang}.vtt")
                if potential_path.exists():
                    sub_path = potential_path
                    break

            return {
                "subtitle": sub_path,
                "title": info.get("title", ""),
                "description": info.get("description", ""),
                "thumbnail_url": info.get("thumbnail") or None,
            }
    except exceptions.VideoDownloadError:
        raise
    except Exception as e:
        raise exceptions.VideoDownloadError(f"Failed to download video: {e}") from e


def read_subtitles(video_data: TranscribedAudio) -> str:
    """Reads the downloaded subtitle file, if there is one. Returns an empty string on failure."""

    subtitle_path = video_data["subtitle"]
    if not subtitle_path:
        return ""

    try:
        with open(subtitle_path, encoding="utf-8") as f:
            subtitle_content = f.read()

        return parse_subtitle_content(subtitle_content)
    except Exception:
        logger.exception("Failed to read subtitles")
        return ""


def resolve_transcription(video_data: TranscribedAudio) -> str:
    """
    Returns the video's subtitles, if yt-dlp found any. Mealie doesn't transcribe a video's
    audio with AI - that would mean downloading and transcribing every video's full audio
    track just to check whether it happens to contain a recipe.
    """

    return read_subtitles(video_data)
