from mealie.core.root_logger import get_logger
from mealie.schema.openai.recipe import OpenAIRecipe
from mealie.schema.recipe.recipe import Recipe
from mealie.schema.recipe.recipe_ingredient import MeasurementSystem
from mealie.services.scraper import cleaner

from ..base import WorkflowStep
from ..context import WorkflowContext
from ..recipe_conversion import to_openai_recipe, to_recipe

CONVERT_MEASUREMENT_SYSTEM_PROMPT = "recipes.convert-measurement-system"

TARGET_LABELS = {
    MeasurementSystem.METRIC: "metric (grams, milliliters, Celsius)",
    MeasurementSystem.US: "US customary (cups, ounces, pounds, Fahrenheit)",
}

logger = get_logger()


class ConvertMeasurementSystemStep(WorkflowStep):
    """
    Converts the draft recipe's measurements to the household's default measurement system.

    Conversion is its own request rather than a clause bolted onto the build prompt, for the same
    reason translation is: neither prompt has to hedge about the other, and the recipe being
    converted is already structured.

    The step is optional. A conversion that fails leaves the recipe in its original units, which
    is worth more to the user than discarding an import that otherwise succeeded.
    """

    name = "convert-measurement-system"
    progress_key = "recipe.create-progress.converting-measurements"
    required = False

    def should_run(self, ctx: WorkflowContext) -> bool:
        if not ctx.draft_recipe or not ctx.options.convert_measurement_system:
            return False

        preferences = ctx.household.preferences if ctx.household else None
        target = preferences.default_measurement_system if preferences else None
        if not target:
            return False

        # nothing to do when the source already predominantly uses the target system
        source = ctx.compiled_source.measurement_system if ctx.compiled_source else None
        return target != source

    def _build_message(self, ctx: WorkflowContext, recipe: Recipe, target: MeasurementSystem) -> str:
        convertible = to_openai_recipe(recipe)

        return "\n\n".join(
            [
                f"Convert the recipe below to the {TARGET_LABELS[target]} measurement system.",
                convertible.model_dump_json(exclude_none=True),
            ]
        )

    async def run(self, ctx: WorkflowContext) -> None:
        recipe = ctx.draft_recipe
        preferences = ctx.household.preferences if ctx.household else None
        target = preferences.default_measurement_system if preferences else None
        if not (recipe and target):
            return

        response = await ctx.ai.get_response(
            ctx.ai.get_prompt(CONVERT_MEASUREMENT_SYSTEM_PROMPT),
            self._build_message(ctx, recipe, target),
            response_schema=OpenAIRecipe,
        )

        if not (response and (response.ingredients or response.instructions)):
            # a conversion that came back empty would lose the recipe, so keep the original
            logger.error("Measurement conversion returned no recipe, keeping the original units")
            return

        converted = to_recipe(ctx, response)
        # nutrition and structured times never made the round trip, so they carry over untouched
        converted.nutrition = recipe.nutrition
        converted.total_time_seconds = recipe.total_time_seconds
        converted.prep_time_seconds = recipe.prep_time_seconds
        converted.perform_time_seconds = recipe.perform_time_seconds

        # cleaning again is what parses the converted quantities and units back out of their new wording
        ctx.draft_recipe = cleaner.clean(converted, ctx.translator)
