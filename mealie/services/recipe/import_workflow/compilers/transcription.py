import asyncio

from mealie.core.dependencies.dependencies import get_temporary_path
from mealie.schema.openai.compiled_source import OpenAICompiledSource
from mealie.services.openai import transcription

from .base import SourceCompiler, SourceType


class TranscriptionCompiler(SourceCompiler):
    """
    Compiles a video into its title, description, and thumbnail, plus its subtitles unless the
    caller has asked to exclude them. The video is always downloaded for its metadata and image
    regardless of that setting - Mealie doesn't transcribe a video's audio with AI, so subtitles
    are the only optional part. A video with nothing useful in title/description/subtitles
    compiles to nothing.
    """

    source_type = SourceType.URL
    progress_key = "recipe.create-progress.downloading-video"

    def _url(self) -> str | None:
        return self.ctx.resolved_url or self.ctx.input.url

    def can_compile(self) -> bool:
        url = self._url()
        if not url:
            return False

        return transcription.is_video_url(url)

    async def compile(self) -> OpenAICompiledSource | None:
        url = self._url() or ""

        with get_temporary_path() as temp_path:
            video_data = await asyncio.to_thread(transcription.download_video, url, temp_path)

        transcript = transcription.resolve_transcription(video_data) if self.ctx.options.include_transcription else ""

        content_parts = [f"# {video_data['title']}"] if video_data["title"] else []
        if video_data["description"]:
            content_parts.append(f"## Video description\n\n{video_data['description']}")
        if transcript:
            content_parts.append(f"## Video subtitles\n\n{transcript}")

        if not content_parts:
            self.logger.error("Could not extract a title, description, or subtitles from the video")
            return None

        return OpenAICompiledSource(
            contains_recipe=True,
            content="\n\n".join(content_parts),
            language=None,
            image_url=video_data["thumbnail_url"],
        )
