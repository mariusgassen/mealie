from mealie.core.root_logger import get_logger
from mealie.schema.openai.recipe import OpenAIRecipe
from mealie.schema.recipe.recipe import Recipe
from mealie.services.scraper import cleaner

from ..base import WorkflowStep
from ..context import WorkflowContext
from ..recipe_conversion import to_openai_recipe, to_recipe

TRANSLATE_RECIPE_PROMPT = "recipes.translate-recipe"

logger = get_logger()


class TranslateRecipeStep(WorkflowStep):
    """
    Translates the draft recipe into the language the caller asked for.

    Translating is its own request rather than a clause bolted onto the build prompt, so that
    neither prompt has to hedge about the other and the recipe being translated is already
    structured: the provider is handed discrete fields to translate instead of being asked to
    extract and translate in one pass.

    The step is optional. A translation that fails leaves an untranslated recipe behind, which
    is worth more to the user than discarding an import that otherwise succeeded.
    """

    name = "translate-recipe"
    progress_key = "recipe.create-progress.translating-recipe"
    required = False

    def should_run(self, ctx: WorkflowContext) -> bool:
        language = ctx.options.translate_language
        if not (language and ctx.draft_recipe):
            return False

        # nothing to do when the source is already written in the target language
        source_language = ctx.compiled_source.language if ctx.compiled_source else None
        return language.lower() != (source_language or "").lower()

    def _build_message(self, ctx: WorkflowContext, recipe: Recipe) -> str:
        translatable = to_openai_recipe(recipe)

        return "\n\n".join(
            [
                f"Translate the recipe below into {ctx.options.translate_language}.",
                translatable.model_dump_json(exclude_none=True),
            ]
        )

    async def run(self, ctx: WorkflowContext) -> None:
        recipe = ctx.draft_recipe
        if not recipe:
            return

        response = await ctx.ai.get_response(
            ctx.ai.get_prompt(TRANSLATE_RECIPE_PROMPT),
            self._build_message(ctx, recipe),
            response_schema=OpenAIRecipe,
        )

        if not (response and (response.ingredients or response.instructions)):
            # a translation that came back empty would lose the recipe, so keep the original
            logger.error("Translation returned no recipe, keeping the untranslated one")
            return

        translated = to_recipe(ctx, response)
        # nutrition and structured times never made the round trip, so they carry over untouched
        translated.nutrition = recipe.nutrition
        translated.total_time_seconds = recipe.total_time_seconds
        translated.prep_time_seconds = recipe.prep_time_seconds
        translated.perform_time_seconds = recipe.perform_time_seconds

        # cleaning again is what parses the translated times and yield back out of their new wording
        ctx.draft_recipe = cleaner.clean(translated, ctx.translator)
