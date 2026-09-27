import json
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

import mealie.services.openai.transcription as transcription_module
import mealie.services.scraper.recipe_scraper as recipe_scraper_module
from mealie.core import exceptions
from mealie.pkgs.safehttp.fetch import FetchResult
from mealie.schema.group.ai_providers import AIProviderCreate, AIProviderSettingsUpdate
from mealie.schema.openai.recipe import OpenAIRecipe, OpenAIRecipeIngredient, OpenAIRecipeInstruction
from mealie.services.openai import OpenAIService
from mealie.services.scraper.scraper_strategies import RecipeScraperOpenAITranscription
from tests.utils import api_routes
from tests.utils.factories import random_int, random_string
from tests.utils.fixture_schemas import TestUser

VIDEO_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


def _make_openai_recipe() -> OpenAIRecipe:
    return OpenAIRecipe(
        name=random_string(),
        description=random_string(),
        ingredients=[OpenAIRecipeIngredient(text=random_string()) for _ in range(random_int(2, 5))],
        instructions=[OpenAIRecipeInstruction(text=random_string()) for _ in range(random_int(2, 5))],
    )


@pytest.fixture(autouse=True)
def video_scraper_setup(monkeypatch: pytest.MonkeyPatch, unique_user: TestUser):
    # Restrict to only the video scraper so other strategies don't interfere
    monkeypatch.setattr(recipe_scraper_module, "DEFAULT_SCRAPER_STRATEGIES", [RecipeScraperOpenAITranscription])

    provider = unique_user.repos.group_ai_providers.create(
        AIProviderCreate(name=random_string(), model="gpt-4o", api_key="test-key")
    )
    unique_user.repos.group_ai_provider_settings.update(
        unique_user.repos.group_id,
        AIProviderSettingsUpdate(
            default_provider_id=provider.id,
            audio_provider_id=provider.id,
            image_provider_id=None,
        ),
    )

    # Prevent any real HTTP calls during scraping
    async def mock_resilient_fetch(url: str) -> FetchResult:
        return FetchResult(b"<html></html>", 200, url, httpx.Headers(), "utf-8")

    monkeypatch.setattr(recipe_scraper_module, "resilient_fetch", mock_resilient_fetch)


def test_create_recipe_from_video(
    api_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    unique_user: TestUser,
    tmp_path: Path,
):
    """Whisper transcription is gone, so this strategy's happy path only exists when the video
    already has subtitles - a video with none falls through to RecipeScraperOpenAI instead."""

    openai_recipe = _make_openai_recipe()

    subtitle_text = random_string()
    subtitle_file = tmp_path / "mealie.en.vtt"
    subtitle_file.write_text(f"WEBVTT\n\n1\n00:00:01.000 --> 00:00:03.000\n{subtitle_text}\n")

    def mock_download_video(url: str, temp_path: Path):
        return {
            "subtitle": subtitle_file,
            "title": random_string(),
            "description": random_string(),
            "thumbnail_url": "https://example.com/thumbnail.jpg",
        }

    # transcribe_audio must NOT be called: Whisper transcription is disabled
    async def mock_transcribe_audio(self, audio_file_path: Path) -> str | None:
        raise AssertionError("transcribe_audio should never be called")

    async def mock_get_response(self, prompt, message, *args, **kwargs) -> OpenAIRecipe | None:
        assert subtitle_text in message
        return openai_recipe

    monkeypatch.setattr(transcription_module, "download_video", mock_download_video)
    monkeypatch.setattr(OpenAIService, "transcribe_audio", mock_transcribe_audio)
    monkeypatch.setattr(OpenAIService, "get_response", mock_get_response)

    r = api_client.post(api_routes.recipes_create_url, json={"url": VIDEO_URL}, headers=unique_user.token)
    assert r.status_code == 201

    slug = json.loads(r.text)
    r = api_client.get(api_routes.recipes_slug(slug), headers=unique_user.token)
    assert r.status_code == 200

    recipe = r.json()
    assert recipe["name"] == openai_recipe.name
    assert len(recipe["recipeIngredient"]) == len(openai_recipe.ingredients)
    assert len(recipe["recipeInstructions"]) == len(openai_recipe.instructions)


def test_create_recipe_from_video_without_subtitles_finds_no_transcript(
    api_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    unique_user: TestUser,
):
    """Without subtitles and without Whisper, this strategy has no transcript to work with and
    should decline rather than call an AI provider with nothing useful to say."""

    def mock_download_video(url: str, temp_path: Path):
        return {
            "subtitle": None,
            "title": random_string(),
            "description": random_string(),
            "thumbnail_url": None,
        }

    async def mock_get_response(self, prompt, message, *args, **kwargs) -> OpenAIRecipe | None:
        raise AssertionError("get_response should never be called without a transcript")

    monkeypatch.setattr(transcription_module, "download_video", mock_download_video)
    monkeypatch.setattr(OpenAIService, "get_response", mock_get_response)

    r = api_client.post(api_routes.recipes_create_url, json={"url": VIDEO_URL}, headers=unique_user.token)
    assert r.status_code == 400


def test_create_recipe_from_video_transcription_disabled(
    api_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    unique_user: TestUser,
):
    unique_user.repos.group_ai_provider_settings.update(
        unique_user.repos.group_id,
        AIProviderSettingsUpdate(default_provider_id=None, audio_provider_id=None, image_provider_id=None),
    )

    r = api_client.post(api_routes.recipes_create_url, json={"url": VIDEO_URL}, headers=unique_user.token)
    assert r.status_code == 400


def test_create_recipe_from_video_without_a_dedicated_audio_provider(
    api_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    unique_user: TestUser,
    tmp_path: Path,
):
    """A dedicated audio provider is no longer required at all: subtitle-based transcription
    needs no AI provider, only the group's regular default provider."""

    current_settings = unique_user.repos.group_ai_provider_settings.get_one(unique_user.repos.group_id)
    unique_user.repos.group_ai_provider_settings.update(
        unique_user.repos.group_id,
        AIProviderSettingsUpdate(
            default_provider_id=current_settings.default_provider_id,
            audio_provider_id=None,
            image_provider_id=current_settings.image_provider_id,
        ),
    )

    openai_recipe = _make_openai_recipe()

    subtitle_file = tmp_path / "mealie.en.vtt"
    subtitle_file.write_text(f"WEBVTT\n\n1\n00:00:01.000 --> 00:00:03.000\n{random_string()}\n")

    def mock_download_video(url: str, temp_path: Path):
        return {
            "subtitle": subtitle_file,
            "title": random_string(),
            "description": random_string(),
            "thumbnail_url": None,
        }

    async def mock_get_response(self, prompt, message, *args, **kwargs) -> OpenAIRecipe | None:
        return openai_recipe

    monkeypatch.setattr(transcription_module, "download_video", mock_download_video)
    monkeypatch.setattr(OpenAIService, "get_response", mock_get_response)

    r = api_client.post(api_routes.recipes_create_url, json={"url": VIDEO_URL}, headers=unique_user.token)
    assert r.status_code == 201


def test_create_recipe_from_video_download_error(
    api_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    unique_user: TestUser,
):
    def mock_download_video(url: str, temp_path: Path):
        raise exceptions.VideoDownloadError("Mock video download error")

    monkeypatch.setattr(transcription_module, "download_video", mock_download_video)

    r = api_client.post(api_routes.recipes_create_url, json={"url": VIDEO_URL}, headers=unique_user.token)
    assert r.status_code == 400


def test_create_recipe_from_video_empty_openai_response(
    api_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    unique_user: TestUser,
    tmp_path: Path,
):
    subtitle_file = tmp_path / "mealie.en.vtt"
    subtitle_file.write_text(f"WEBVTT\n\n1\n00:00:01.000 --> 00:00:03.000\n{random_string()}\n")

    def mock_download_video(url: str, temp_path: Path):
        return {
            "subtitle": subtitle_file,
            "title": random_string(),
            "description": random_string(),
            "thumbnail_url": None,
        }

    async def mock_get_response(self, prompt, message, *args, **kwargs) -> OpenAIRecipe | None:
        return None

    monkeypatch.setattr(transcription_module, "download_video", mock_download_video)
    monkeypatch.setattr(OpenAIService, "get_response", mock_get_response)

    r = api_client.post(api_routes.recipes_create_url, json={"url": VIDEO_URL}, headers=unique_user.token)
    assert r.status_code == 400
