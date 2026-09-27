"""
Integration tests for admin AI prompt override management across groups.
"""

from fastapi.testclient import TestClient

from tests.utils import api_routes
from tests.utils.factories import random_string
from tests.utils.fixture_schemas import TestUser

KNOWN_PROMPT = "recipes.parse-recipe-ingredients"


def test_admin_ai_prompt_routes_require_admin(api_client: TestClient, unique_user: TestUser, admin_user: TestUser):
    """Non-admin users cannot access admin AI prompt routes, even for their own group."""
    response = api_client.get(
        api_routes.admin_groups_group_id_ai_providers_prompts(unique_user.group_id),
        headers=unique_user.token,
    )
    assert response.status_code == 403


def test_admin_list_ai_prompts_for_group(api_client: TestClient, admin_user: TestUser, unique_user: TestUser):
    """Admin can list the AI prompts for any group."""
    response = api_client.get(
        api_routes.admin_groups_group_id_ai_providers_prompts(unique_user.group_id),
        headers=admin_user.token,
    )
    assert response.status_code == 200

    prompts = response.json()
    names = [p["name"] for p in prompts]
    assert KNOWN_PROMPT in names


def test_admin_get_ai_prompt_for_group(api_client: TestClient, admin_user: TestUser, unique_user: TestUser):
    """Admin can retrieve a single AI prompt for any group."""
    response = api_client.get(
        api_routes.admin_groups_group_id_ai_providers_prompts_name(unique_user.group_id, KNOWN_PROMPT),
        headers=admin_user.token,
    )
    assert response.status_code == 200

    prompt = response.json()
    assert prompt["name"] == KNOWN_PROMPT
    assert prompt["isOverridden"] is False


def test_admin_get_ai_prompt_not_found(api_client: TestClient, admin_user: TestUser, unique_user: TestUser):
    response = api_client.get(
        api_routes.admin_groups_group_id_ai_providers_prompts_name(unique_user.group_id, "not.a.real.prompt"),
        headers=admin_user.token,
    )
    assert response.status_code == 404


def test_admin_update_ai_prompt_for_group(api_client: TestClient, admin_user: TestUser, unique_user: TestUser):
    """Admin can override an AI prompt for any group."""
    try:
        response = api_client.put(
            api_routes.admin_groups_group_id_ai_providers_prompts_name(unique_user.group_id, KNOWN_PROMPT),
            json={"prompt": "ADMIN CUSTOM PROMPT"},
            headers=admin_user.token,
        )
        assert response.status_code == 200

        prompt = response.json()
        assert prompt["content"] == "ADMIN CUSTOM PROMPT"
        assert prompt["isOverridden"] is True
    finally:
        api_client.delete(
            api_routes.admin_groups_group_id_ai_providers_prompts_name(unique_user.group_id, KNOWN_PROMPT),
            headers=admin_user.token,
        )


def test_admin_reset_ai_prompt_for_group(api_client: TestClient, admin_user: TestUser, unique_user: TestUser):
    """Admin can reset a group's AI prompt override back to the default."""
    api_client.put(
        api_routes.admin_groups_group_id_ai_providers_prompts_name(unique_user.group_id, KNOWN_PROMPT),
        json={"prompt": "ADMIN CUSTOM PROMPT"},
        headers=admin_user.token,
    )

    response = api_client.delete(
        api_routes.admin_groups_group_id_ai_providers_prompts_name(unique_user.group_id, KNOWN_PROMPT),
        headers=admin_user.token,
    )
    assert response.status_code == 200

    prompt = response.json()
    assert prompt["isOverridden"] is False


def test_admin_can_manage_prompts_across_groups(api_client: TestClient, admin_user: TestUser):
    """Admin can override prompts in a group they are not a member of."""
    group_name = random_string()
    create_resp = api_client.post(api_routes.admin_groups, json={"name": group_name}, headers=admin_user.token)
    assert create_resp.status_code == 201
    foreign_group_id = create_resp.json()["id"]

    try:
        response = api_client.put(
            api_routes.admin_groups_group_id_ai_providers_prompts_name(foreign_group_id, KNOWN_PROMPT),
            json={"prompt": "CROSS GROUP PROMPT"},
            headers=admin_user.token,
        )
        assert response.status_code == 200
        assert response.json()["content"] == "CROSS GROUP PROMPT"
    finally:
        api_client.delete(api_routes.admin_groups_item_id(foreign_group_id), headers=admin_user.token)
