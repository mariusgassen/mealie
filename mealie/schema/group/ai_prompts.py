from pydantic import UUID4, ConfigDict, field_validator

from mealie.schema._mealie import MealieModel


class AIPromptOverrideCreate(MealieModel):
    name: str
    prompt: str

    @field_validator("name", "prompt")
    def validate_not_empty(cls, val: str) -> str:
        if not val:
            raise ValueError("Value cannot be empty")

        return val


class AIPromptOverrideSave(AIPromptOverrideCreate):
    group_id: UUID4


class AIPromptOverrideUpdate(MealieModel):
    prompt: str

    @field_validator("prompt")
    def validate_not_empty(cls, val: str) -> str:
        if not val:
            raise ValueError("Value cannot be empty")

        return val


class AIPromptOverrideOut(AIPromptOverrideCreate):
    id: UUID4

    model_config = ConfigDict(from_attributes=True)


class AIPromptOut(MealieModel):
    """
    A single AI prompt, identified by its dotted name (e.g. `recipes.parse-recipe-ingredients`).

    `content` is the prompt actually used (the override when one is set, otherwise
    `default_content`), while `default_content` is always the non-override baseline shipped with
    or configured for the server, so the editor can offer a "reset to default" action.
    """

    name: str
    content: str
    default_content: str
    is_overridden: bool
