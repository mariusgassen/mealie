from unittest.mock import AsyncMock, Mock

import pytest

import mealie.services.openai.transcription as transcription_module
from mealie.services.openai import transcription
from mealie.services.recipe.import_workflow.compilers.transcription import TranscriptionCompiler


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", True),
        ("https://www.facebook.com/reel/1433866715330175/", True),
        ("https://www.facebook.com/share/r/1DWziuVHRi/", False),
        ("https://example.com/recipe", False),
        ("", False),
    ],
)
def test_is_video_url(url: str, expected: bool):
    """
    yt-dlp's Facebook extractor matches /reel/ but not /share/r/ share links.
    Those are handled by following redirects in the import workflow.
    """

    assert transcription.is_video_url(url) is expected


def test_transcription_compiler_uses_resolved_url(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        transcription,
        "is_video_url",
        lambda url: url == "https://www.facebook.com/reel/1433866715330175/",
    )

    ctx = Mock()
    ctx.input.url = "https://www.facebook.com/share/r/1DWziuVHRi/"
    ctx.resolved_url = "https://www.facebook.com/reel/1433866715330175/"

    compiler = TranscriptionCompiler(ctx)
    assert compiler.can_compile() is True
    assert compiler._url() == ctx.resolved_url


def test_transcription_compiler_can_compile_regardless_of_options(monkeypatch: pytest.MonkeyPatch):
    """include_transcription only controls whether subtitles are used, not whether the video
    is compiled at all - metadata and thumbnail are always fetched."""

    monkeypatch.setattr(transcription, "is_video_url", lambda url: True)

    ctx = Mock()
    ctx.input.url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    ctx.resolved_url = None
    ctx.options.include_transcription = False

    compiler = TranscriptionCompiler(ctx)
    assert compiler.can_compile() is True


def test_transcription_compiler_does_not_require_an_audio_provider(monkeypatch: pytest.MonkeyPatch):
    """Video metadata (title/description/thumbnail) needs no AI provider, so an audio provider
    being unconfigured should no longer block the compiler from running at all."""

    monkeypatch.setattr(transcription, "is_video_url", lambda url: True)

    ctx = Mock()
    ctx.input.url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    ctx.resolved_url = None
    ctx.options.include_transcription = True
    ctx.ai.provider_settings.audio_provider_enabled = False

    compiler = TranscriptionCompiler(ctx)
    assert compiler.can_compile() is True


@pytest.mark.asyncio
async def test_transcription_compiler_falls_back_to_metadata_without_subtitles(monkeypatch: pytest.MonkeyPatch):
    """No subtitles and no Whisper call should still produce a document from the title,
    description, and thumbnail, so the video's image isn't lost."""

    monkeypatch.setattr(
        transcription,
        "download_video",
        lambda url, temp_path: {
            "subtitle": None,
            "title": "A reel",
            "description": "1 cup flour, 2 eggs. Mix and bake.",
            "thumbnail_url": "https://example.com/thumb.jpg",
        },
    )

    ctx = Mock()
    ctx.input.url = "https://www.instagram.com/reel/abc123/"
    ctx.resolved_url = None
    ctx.report_progress = AsyncMock()

    compiler = TranscriptionCompiler(ctx)
    compiled = await compiler.compile()

    assert compiled is not None
    assert compiled.image_url == "https://example.com/thumb.jpg"
    assert "A reel" in compiled.content
    assert "1 cup flour, 2 eggs. Mix and bake." in compiled.content
    assert "Video subtitles" not in compiled.content


@pytest.mark.asyncio
async def test_transcription_compiler_excludes_subtitles_when_disabled(
    monkeypatch: pytest.MonkeyPatch, tmp_path
):
    """Disabling include_transcription drops subtitles even when the video has them - metadata
    and thumbnail are unaffected."""

    subtitle_file = tmp_path / "mealie.en.vtt"
    subtitle_file.write_text("WEBVTT\n\n1\n00:00:01.000 --> 00:00:03.000\nmix flour and water\n")

    monkeypatch.setattr(
        transcription,
        "download_video",
        lambda url, temp_path: {
            "subtitle": subtitle_file,
            "title": "A reel",
            "description": "See caption for recipe.",
            "thumbnail_url": "https://example.com/thumb.jpg",
        },
    )

    ctx = Mock()
    ctx.input.url = "https://www.instagram.com/reel/abc123/"
    ctx.resolved_url = None
    ctx.options.include_transcription = False
    ctx.report_progress = AsyncMock()

    compiler = TranscriptionCompiler(ctx)
    compiled = await compiler.compile()

    assert compiled is not None
    assert compiled.image_url == "https://example.com/thumb.jpg"
    assert "A reel" in compiled.content
    assert "See caption for recipe." in compiled.content
    assert "mix flour and water" not in compiled.content
    assert "Video subtitles" not in compiled.content


@pytest.mark.asyncio
async def test_transcription_compiler_returns_none_with_nothing_usable(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        transcription,
        "download_video",
        lambda url, temp_path: {"subtitle": None, "title": "", "description": "", "thumbnail_url": None},
    )

    ctx = Mock()
    ctx.input.url = "https://www.instagram.com/reel/abc123/"
    ctx.resolved_url = None
    ctx.report_progress = AsyncMock()

    compiler = TranscriptionCompiler(ctx)
    assert await compiler.compile() is None


class _SettingsStub:
    YTDLP_COOKIEFILE: str | None = None


@pytest.fixture()
def settings_stub(monkeypatch):
    s = _SettingsStub()

    def _fake_get_app_settings():
        return s

    monkeypatch.setattr(transcription_module, "get_app_settings", _fake_get_app_settings)
    return s


class _FakeYoutubeDL:
    """Records the ydl_opts it was constructed with instead of hitting the network."""

    last_opts: dict | None = None

    def __init__(self, opts: dict):
        _FakeYoutubeDL.last_opts = opts

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def extract_info(self, url: str, download: bool = True):
        return {"title": "Fake Title", "description": "Fake Description", "thumbnail": None}


@pytest.fixture()
def fake_yt_dlp(monkeypatch):
    _FakeYoutubeDL.last_opts = None
    monkeypatch.setattr("yt_dlp.YoutubeDL", _FakeYoutubeDL)
    return _FakeYoutubeDL


def test_download_video_omits_cookiefile_by_default(settings_stub, fake_yt_dlp, tmp_path):
    transcription_module.download_video("https://example.com/video", tmp_path)

    assert "cookiefile" not in fake_yt_dlp.last_opts


def test_download_video_passes_configured_cookiefile(settings_stub, fake_yt_dlp, tmp_path):
    settings_stub.YTDLP_COOKIEFILE = "/data/cookies.txt"

    transcription_module.download_video("https://example.com/video", tmp_path)

    assert fake_yt_dlp.last_opts["cookiefile"] == "/data/cookies.txt"


def test_download_video_never_downloads_the_media_file(settings_stub, fake_yt_dlp, tmp_path):
    """Only metadata and subtitles are needed now that Whisper transcription is gone, so the
    actual audio/video should never be downloaded."""

    transcription_module.download_video("https://example.com/video", tmp_path)

    assert fake_yt_dlp.last_opts["skip_download"] is True
    assert "postprocessors" not in fake_yt_dlp.last_opts
