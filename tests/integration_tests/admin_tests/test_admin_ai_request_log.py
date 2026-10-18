from uuid import UUID

from fastapi.testclient import TestClient

from mealie.services.openai.request_log import record_request
from tests.utils import api_routes
from tests.utils.fixture_schemas import TestUser


def test_admin_ai_request_log_requires_admin(api_client: TestClient, unique_user: TestUser):
    response = api_client.get(
        api_routes.admin_groups_group_id_ai_providers_request_log(unique_user.group_id), headers=unique_user.token
    )
    assert response.status_code == 403


def test_admin_ai_request_log_lists_and_clears(api_client: TestClient, admin_user: TestUser, unique_user: TestUser):
    url = api_routes.admin_groups_group_id_ai_providers_request_log(unique_user.group_id)
    assert api_client.get(url, headers=admin_user.token).json() == []

    record_request(
        UUID(str(unique_user.group_id)),
        request_type="OpenAIIngredients",
        model="m",
        system_prompt="the prompt",
        user_message="[]",
        raw_response="{}",
    )

    [entry] = api_client.get(url, headers=admin_user.token).json()
    assert entry["systemPrompt"] == "the prompt"

    assert api_client.delete(url, headers=admin_user.token).status_code == 204
    assert api_client.get(url, headers=admin_user.token).json() == []
