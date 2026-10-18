from uuid import UUID

from fastapi.testclient import TestClient

from mealie.services.openai.request_log import record_request
from tests.utils import api_routes
from tests.utils.fixture_schemas import TestUser


def test_request_log_lists_and_clears(api_client: TestClient, unique_user: TestUser):
    assert api_client.get(api_routes.groups_ai_providers_request_log, headers=unique_user.token).json() == []

    record_request(
        UUID(str(unique_user.group_id)),
        request_type="OpenAIIngredients",
        model="m",
        system_prompt="the prompt",
        user_message='["Salz und Pfeffer"]',
        raw_response="{}",
    )

    response = api_client.get(api_routes.groups_ai_providers_request_log, headers=unique_user.token)
    assert response.status_code == 200
    [entry] = response.json()
    assert entry["systemPrompt"] == "the prompt"
    assert entry["rawResponse"] == "{}"

    assert api_client.delete(api_routes.groups_ai_providers_request_log, headers=unique_user.token).status_code == 204
    assert api_client.get(api_routes.groups_ai_providers_request_log, headers=unique_user.token).json() == []
