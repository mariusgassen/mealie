"""
Integration tests for AI prompt overrides: listing the shipped prompts, overriding one, and
resetting it back to the shipped default.
"""

from fastapi.testclient import TestClient

from tests.utils import api_routes
from tests.utils.fixture_schemas import TestUser

KNOWN_PROMPT = "recipes.parse-recipe-ingredients"


def _reset(api_client: TestClient, user: TestUser, name: str = KNOWN_PROMPT) -> None:
    api_client.delete(api_routes.groups_ai_providers_prompts_name(name), headers=user.token)


def test_list_prompts(api_client: TestClient, unique_user: TestUser):
    response = api_client.get(api_routes.groups_ai_providers_prompts, headers=unique_user.token)
    assert response.status_code == 200

    prompts = response.json()
    assert isinstance(prompts, list)
    names = [p["name"] for p in prompts]
    assert KNOWN_PROMPT in names

    prompt = next(p for p in prompts if p["name"] == KNOWN_PROMPT)
    assert prompt["content"] == prompt["defaultContent"]
    assert prompt["isOverridden"] is False


def test_get_prompt(api_client: TestClient, unique_user: TestUser):
    response = api_client.get(api_routes.groups_ai_providers_prompts_name(KNOWN_PROMPT), headers=unique_user.token)
    assert response.status_code == 200

    prompt = response.json()
    assert prompt["name"] == KNOWN_PROMPT
    assert prompt["content"]
    assert prompt["content"] == prompt["defaultContent"]
    assert prompt["isOverridden"] is False


def test_get_prompt_not_found(api_client: TestClient, unique_user: TestUser):
    response = api_client.get(
        api_routes.groups_ai_providers_prompts_name("not.a.real.prompt"), headers=unique_user.token
    )
    assert response.status_code == 404


def test_update_prompt_creates_override(api_client: TestClient, unique_user: TestUser):
    try:
        response = api_client.put(
            api_routes.groups_ai_providers_prompts_name(KNOWN_PROMPT),
            json={"prompt": "CUSTOM PROMPT TEXT"},
            headers=unique_user.token,
        )
        assert response.status_code == 200

        prompt = response.json()
        assert prompt["content"] == "CUSTOM PROMPT TEXT"
        assert prompt["isOverridden"] is True
        assert prompt["defaultContent"] != "CUSTOM PROMPT TEXT"

        # It's persisted, not just echoed back
        get_response = api_client.get(
            api_routes.groups_ai_providers_prompts_name(KNOWN_PROMPT), headers=unique_user.token
        )
        assert get_response.json()["content"] == "CUSTOM PROMPT TEXT"
    finally:
        _reset(api_client, unique_user)


def test_update_prompt_overwrites_existing_override(api_client: TestClient, unique_user: TestUser):
    try:
        api_client.put(
            api_routes.groups_ai_providers_prompts_name(KNOWN_PROMPT),
            json={"prompt": "FIRST VERSION"},
            headers=unique_user.token,
        )
        response = api_client.put(
            api_routes.groups_ai_providers_prompts_name(KNOWN_PROMPT),
            json={"prompt": "SECOND VERSION"},
            headers=unique_user.token,
        )
        assert response.status_code == 200
        assert response.json()["content"] == "SECOND VERSION"
    finally:
        _reset(api_client, unique_user)


def test_update_prompt_not_found(api_client: TestClient, unique_user: TestUser):
    response = api_client.put(
        api_routes.groups_ai_providers_prompts_name("not.a.real.prompt"),
        json={"prompt": "irrelevant"},
        headers=unique_user.token,
    )
    assert response.status_code == 404


def test_reset_prompt_restores_default(api_client: TestClient, unique_user: TestUser):
    default_response = api_client.get(
        api_routes.groups_ai_providers_prompts_name(KNOWN_PROMPT), headers=unique_user.token
    )
    default_content = default_response.json()["defaultContent"]

    api_client.put(
        api_routes.groups_ai_providers_prompts_name(KNOWN_PROMPT),
        json={"prompt": "CUSTOM PROMPT TEXT"},
        headers=unique_user.token,
    )

    response = api_client.delete(api_routes.groups_ai_providers_prompts_name(KNOWN_PROMPT), headers=unique_user.token)
    assert response.status_code == 200

    prompt = response.json()
    assert prompt["isOverridden"] is False
    assert prompt["content"] == default_content


def test_reset_prompt_without_override_is_a_noop(api_client: TestClient, unique_user: TestUser):
    response = api_client.delete(api_routes.groups_ai_providers_prompts_name(KNOWN_PROMPT), headers=unique_user.token)
    assert response.status_code == 200
    assert response.json()["isOverridden"] is False


def test_reset_prompt_not_found(api_client: TestClient, unique_user: TestUser):
    response = api_client.delete(
        api_routes.groups_ai_providers_prompts_name("not.a.real.prompt"), headers=unique_user.token
    )
    assert response.status_code == 404


# ==========================================
# Permissions: can_manage required
# ==========================================


def test_prompts_require_can_manage_list(api_client: TestClient, user_tuple: list[TestUser]):
    usr, _ = user_tuple

    user = usr.repos.users.get_one(usr.user_id)
    assert user
    user.can_manage = False
    usr.repos.users.update(user.id, user)

    response = api_client.get(api_routes.groups_ai_providers_prompts, headers=usr.token)
    assert response.status_code == 403


def test_prompts_require_can_manage_get(api_client: TestClient, user_tuple: list[TestUser]):
    usr, _ = user_tuple

    user = usr.repos.users.get_one(usr.user_id)
    assert user
    user.can_manage = False
    usr.repos.users.update(user.id, user)

    response = api_client.get(api_routes.groups_ai_providers_prompts_name(KNOWN_PROMPT), headers=usr.token)
    assert response.status_code == 403


def test_prompts_require_can_manage_update(api_client: TestClient, user_tuple: list[TestUser]):
    usr, _ = user_tuple

    user = usr.repos.users.get_one(usr.user_id)
    assert user
    user.can_manage = False
    usr.repos.users.update(user.id, user)

    response = api_client.put(
        api_routes.groups_ai_providers_prompts_name(KNOWN_PROMPT), json={"prompt": "irrelevant"}, headers=usr.token
    )
    assert response.status_code == 403


def test_prompts_require_can_manage_reset(api_client: TestClient, user_tuple: list[TestUser]):
    usr, _ = user_tuple

    user = usr.repos.users.get_one(usr.user_id)
    assert user
    user.can_manage = False
    usr.repos.users.update(user.id, user)

    response = api_client.delete(api_routes.groups_ai_providers_prompts_name(KNOWN_PROMPT), headers=usr.token)
    assert response.status_code == 403
