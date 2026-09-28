import asyncio

from mealie.core import exceptions
from mealie.core.dependencies.dependencies import get_temporary_path
from mealie.schema.openai.compiled_source import OpenAICompiledSource
from mealie.services.openai import transcription

from .base import SourceCompiler, SourceType


class TranscriptionCompiler(SourceCompiler):
    """
    Compiles a video into its title, description, and thumbnail, plus a transcript: its
    subtitles if it has any (always used, free), otherwise an AI transcription of its audio if
    the caller allows that fallback. Title, description, and thumbnail are always fetched
    regardless of that setting. A video with nothing useful in any of these compiles to nothing.
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

            async def report_transcribing() -> None:
                await self.ctx.report_progress("recipe.create-progress.transcribing-audio-with-ai")

            try:
                transcript = await transcription.resolve_transcription(
                    url,
                    video_data,
                    temp_path,
                    self.ctx.ai,
                    allow_whisper=self.ctx.options.include_transcription,
                    before_transcribe=report_transcribing,
                )
            except exceptions.RateLimitError:
                raise
            except Exception:
                # the title/description/thumbnail are still worth keeping even if transcribing
                # the audio failed - only actually missing subtitles falls through further up,
                # to reading the page as a webpage instead
                self.logger.exception("Failed to transcribe the video's audio, continuing without a transcript")
                transcript = ""

        content_parts = [f"# {video_data['title']}"] if video_data["title"] else []
        if video_data["description"]:
            content_parts.append(f"## Video description\n\n{video_data['description']}")
        if transcript:
            content_parts.append(f"## Video transcript\n\n{transcript}")

        if not content_parts:
            self.logger.error("Could not extract a title, description, or transcript from the video")
            return None

        return OpenAICompiledSource(
            contains_recipe=True,
            content="\n\n".join(content_parts),
            language=None,
            image_url=video_data["thumbnail_url"],
        )
