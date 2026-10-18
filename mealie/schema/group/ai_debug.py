from datetime import datetime

from mealie.schema._mealie import MealieModel


class AIRequestLogEntry(MealieModel):
    """
    One request sent to an AI provider, with exactly what was sent and what came back, so a
    group manager can check which prompt actually reached the model and how it answered.
    """

    timestamp: datetime
    request_type: str
    model: str
    system_prompt: str
    user_message: str
    raw_response: str | None = None
    error: str | None = None
