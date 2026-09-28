from unittest.mock import AsyncMock, Mock

import pytest

import mealie.services.openai.transcription as transcription_module
from mealie.core import exceptions
from mealie.services.openai import transcription
from mealie.services.recipe.import_workflow.compilers.transcription import TranscriptionCompiler

VIDEO_URL = "https://example.com/video"


def _subtitle_file(tmp_path, text: str = "mix flour and water"):
    subtitle_file = tmp_path / "mealie.en.vtt"
    subtitle_file.write_text(f"WEBVTT\n\n1\n00:00:01.000 --> 00:00:03.000\n{text}\n")
    return subtitle_file


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
    """include_transcription only controls what happens when a video has no subtitles, not
    whether the video is compiled at all - metadata and thumbnail are always fetched."""

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
    """No subtitles and transcription disabled should still produce a document from the title,
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
    ctx.options.include_transcription = False
    ctx.report_progress = AsyncMock()

    compiler = TranscriptionCompiler(ctx)
    compiled = await compiler.compile()

    assert compiled is not None
    assert compiled.image_url == "https://example.com/thumb.jpg"
    assert "A reel" in compiled.content
    assert "1 cup flour, 2 eggs. Mix and bake." in compiled.content
    assert "Video transcript" not in compiled.content


@pytest.mark.asyncio
async def test_transcription_compiler_uses_subtitles_regardless_of_options(monkeypatch: pytest.MonkeyPatch, tmp_path):
    """Subtitles are free, so they're used whether include_transcription is on or off - the
    setting only controls the Whisper fallback for videos with no subtitles."""

    subtitle_file = _subtitle_file(tmp_path)

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

    for include_transcription in (True, False):
        ctx = Mock()
        ctx.input.url = "https://www.instagram.com/reel/abc123/"
        ctx.resolved_url = None
        ctx.options.include_transcription = include_transcription
        ctx.report_progress = AsyncMock()
        ctx.ai.transcribe_audio = AsyncMock(side_effect=AssertionError("Whisper should not be called"))

        compiler = TranscriptionCompiler(ctx)
        compiled = await compiler.compile()

        assert compiled is not None
        assert "mix flour and water" in compiled.content


@pytest.mark.asyncio
async def test_transcription_compiler_skips_whisper_when_disabled(monkeypatch: pytest.MonkeyPatch):
    """No subtitles and transcription disabled means no transcript at all - Whisper is never
    attempted."""

    monkeypatch.setattr(
        transcription,
        "download_video",
        lambda url, temp_path: {
            "subtitle": None,
            "title": "A reel",
            "description": "See caption for recipe.",
            "thumbnail_url": None,
        },
    )

    def fail_if_called(url, temp_path):
        raise AssertionError("download_audio should not be called when include_transcription is False")

    monkeypatch.setattr(transcription, "download_audio", fail_if_called)

    ctx = Mock()
    ctx.input.url = "https://www.instagram.com/reel/abc123/"
    ctx.resolved_url = None
    ctx.options.include_transcription = False
    ctx.report_progress = AsyncMock()

    compiler = TranscriptionCompiler(ctx)
    compiled = await compiler.compile()

    assert compiled is not None
    assert "Video transcript" not in compiled.content


@pytest.mark.asyncio
async def test_transcription_compiler_falls_back_to_whisper_when_enabled(monkeypatch: pytest.MonkeyPatch, tmp_path):
    """No subtitles and transcription enabled falls back to transcribing the audio with AI."""

    monkeypatch.setattr(
        transcription,
        "download_video",
        lambda url, temp_path: {
            "subtitle": None,
            "title": "A reel",
            "description": "See caption for recipe.",
            "thumbnail_url": None,
        },
    )
    monkeypatch.setattr(transcription, "download_audio", lambda url, temp_path: tmp_path / "mealie.mp3")

    ctx = Mock()
    ctx.input.url = "https://www.instagram.com/reel/abc123/"
    ctx.resolved_url = None
    ctx.options.include_transcription = True
    ctx.report_progress = AsyncMock()
    ctx.ai.transcribe_audio = AsyncMock(return_value="whispered transcript")

    compiler = TranscriptionCompiler(ctx)
    compiled = await compiler.compile()

    assert compiled is not None
    assert "whispered transcript" in compiled.content
    ctx.ai.transcribe_audio.assert_awaited_once()


@pytest.mark.asyncio
async def test_transcription_compiler_keeps_metadata_when_whisper_fails(monkeypatch: pytest.MonkeyPatch, tmp_path):
    """A Whisper failure shouldn't lose the title/description/thumbnail already fetched for
    free - only the transcript is missing."""

    monkeypatch.setattr(
        transcription,
        "download_video",
        lambda url, temp_path: {
            "subtitle": None,
            "title": "A reel",
            "description": "See caption for recipe.",
            "thumbnail_url": "https://example.com/thumb.jpg",
        },
    )
    monkeypatch.setattr(transcription, "download_audio", lambda url, temp_path: tmp_path / "mealie.mp3")

    ctx = Mock()
    ctx.input.url = "https://www.instagram.com/reel/abc123/"
    ctx.resolved_url = None
    ctx.options.include_transcription = True
    ctx.report_progress = AsyncMock()
    ctx.ai.transcribe_audio = AsyncMock(side_effect=Exception("boom"))

    compiler = TranscriptionCompiler(ctx)
    compiled = await compiler.compile()

    assert compiled is not None
    assert compiled.image_url == "https://example.com/thumb.jpg"
    assert "See caption for recipe." in compiled.content
    assert "Video transcript" not in compiled.content


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
    ctx.options.include_transcription = False
    ctx.report_progress = AsyncMock()

    compiler = TranscriptionCompiler(ctx)
    assert await compiler.compile() is None


@pytest.mark.asyncio
async def test_resolve_transcription_prefers_subtitles_regardless_of_allow_whisper(tmp_path):
    subtitle_file = _subtitle_file(tmp_path)
    video_data = {"subtitle": subtitle_file, "title": "T", "description": "D", "thumbnail_url": None}

    openai_service = Mock()
    openai_service.transcribe_audio = AsyncMock(side_effect=AssertionError("Whisper should not be called"))

    for allow_whisper in (True, False):
        result = await transcription.resolve_transcription(
            VIDEO_URL, video_data, tmp_path, openai_service, allow_whisper=allow_whisper
        )
        assert result == "mix flour and water"

    openai_service.transcribe_audio.assert_not_called()


@pytest.mark.asyncio
async def test_resolve_transcription_skips_whisper_when_not_allowed(monkeypatch: pytest.MonkeyPatch, tmp_path):
    video_data = {"subtitle": None, "title": "T", "description": "D", "thumbnail_url": None}

    def fail_if_called(url, temp_path):
        raise AssertionError("download_audio should not be called when allow_whisper is False")

    monkeypatch.setattr(transcription, "download_audio", fail_if_called)

    result = await transcription.resolve_transcription(VIDEO_URL, video_data, tmp_path, Mock(), allow_whisper=False)
    assert result == ""


@pytest.mark.asyncio
async def test_resolve_transcription_falls_back_to_whisper_when_allowed(monkeypatch: pytest.MonkeyPatch, tmp_path):
    video_data = {"subtitle": None, "title": "T", "description": "D", "thumbnail_url": None}
    audio_path = tmp_path / "mealie.mp3"

    monkeypatch.setattr(transcription, "download_audio", lambda url, temp_path: audio_path)

    openai_service = Mock()
    openai_service.transcribe_audio = AsyncMock(return_value="whispered transcript")
    before_transcribe = AsyncMock()

    result = await transcription.resolve_transcription(
        VIDEO_URL,
        video_data,
        tmp_path,
        openai_service,
        allow_whisper=True,
        before_transcribe=before_transcribe,
    )

    assert result == "whispered transcript"
    openai_service.transcribe_audio.assert_awaited_once_with(audio_path)
    before_transcribe.assert_awaited_once()


@pytest.mark.asyncio
async def test_resolve_transcription_raises_when_whisper_returns_nothing(monkeypatch: pytest.MonkeyPatch, tmp_path):
    video_data = {"subtitle": None, "title": "T", "description": "D", "thumbnail_url": None}
    monkeypatch.setattr(transcription, "download_audio", lambda url, temp_path: tmp_path / "mealie.mp3")

    openai_service = Mock()
    openai_service.transcribe_audio = AsyncMock(return_value=None)

    with pytest.raises(exceptions.OpenAIServiceError):
        await transcription.resolve_transcription(VIDEO_URL, video_data, tmp_path, openai_service, allow_whisper=True)


@pytest.mark.asyncio
async def test_resolve_transcription_propagates_rate_limit_errors(monkeypatch: pytest.MonkeyPatch, tmp_path):
    video_data = {"subtitle": None, "title": "T", "description": "D", "thumbnail_url": None}
    monkeypatch.setattr(transcription, "download_audio", lambda url, temp_path: tmp_path / "mealie.mp3")

    openai_service = Mock()
    openai_service.transcribe_audio = AsyncMock(side_effect=exceptions.RateLimitError("slow down"))

    with pytest.raises(exceptions.RateLimitError):
        await transcription.resolve_transcription(VIDEO_URL, video_data, tmp_path, openai_service, allow_whisper=True)


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
    """download_video only fetches metadata and subtitles - the audio/video file is only
    downloaded separately, by download_audio, when Whisper transcription is actually needed."""

    transcription_module.download_video("https://example.com/video", tmp_path)

    assert fake_yt_dlp.last_opts["skip_download"] is True
    assert "postprocessors" not in fake_yt_dlp.last_opts


def test_download_audio_downloads_the_media_file(settings_stub, fake_yt_dlp, tmp_path):
    """download_audio is only called as the Whisper fallback, so unlike download_video it must
    actually fetch the audio track."""

    transcription_module.download_audio("https://example.com/video", tmp_path)

    assert fake_yt_dlp.last_opts["skip_download"] is False
    assert fake_yt_dlp.last_opts["format"] == "bestaudio/best"
    assert fake_yt_dlp.last_opts["postprocessors"][0]["key"] == "FFmpegExtractAudio"
