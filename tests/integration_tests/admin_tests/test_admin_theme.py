"""
Integration tests for the server-wide theme that admins can edit.
"""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from mealie.core.config import get_app_settings
from tests.utils import api_routes
from tests.utils.fixture_schemas import TestUser


@pytest.fixture(autouse=True)
def reset_theme(api_client: TestClient, admin_user: TestUser) -> Generator[None]:
    """Theme overrides are server-wide, so make sure no test leaks them into the next one"""
    api_client.delete(api_routes.admin_theme, headers=admin_user.token)
    yield
    api_client.delete(api_routes.admin_theme, headers=admin_user.token)


def test_admin_theme_routes_require_admin(api_client: TestClient, unique_user: TestUser):
    assert api_client.get(api_routes.admin_theme, headers=unique_user.token).status_code == 403
    assert api_client.put(api_routes.admin_theme, json={}, headers=unique_user.token).status_code == 403
    assert api_client.delete(api_routes.admin_theme, headers=unique_user.token).status_code == 403


def test_admin_get_theme_without_overrides(api_client: TestClient, admin_user: TestUser):
    response = api_client.get(api_routes.admin_theme, headers=admin_user.token)
    assert response.status_code == 200

    data = response.json()
    assert data["overridden"] == []
    assert data["theme"] == data["defaults"]

    configured = get_app_settings().theme
    assert data["defaults"]["darkPrimary"] == configured.dark_primary
    assert data["defaults"]["lightBackground"] == configured.light_background
    assert data["defaults"]["darkSurface"] == configured.dark_surface


def test_admin_update_theme_sets_only_what_is_sent(api_client: TestClient, admin_user: TestUser):
    response = api_client.put(
        api_routes.admin_theme,
        json={"darkPrimary": "#112233", "lightBackground": "#abcdef"},
        headers=admin_user.token,
    )
    assert response.status_code == 200

    data = response.json()
    assert data["overridden"] == ["darkPrimary", "lightBackground"]
    assert data["theme"]["darkPrimary"] == "#112233"
    # colors are normalised to upper case
    assert data["theme"]["lightBackground"] == "#ABCDEF"
    # everything else is untouched
    assert data["theme"]["lightPrimary"] == data["defaults"]["lightPrimary"]
    # the defaults behind the overrides are still reported unchanged
    assert data["defaults"]["darkPrimary"] == get_app_settings().theme.dark_primary


def test_public_theme_reflects_admin_overrides(api_client: TestClient, admin_user: TestUser):
    api_client.put(api_routes.admin_theme, json={"darkPrimary": "#445566"}, headers=admin_user.token)

    # no auth header: the frontend reads this before anyone has logged in
    response = api_client.get(api_routes.app_about_theme)
    assert response.status_code == 200
    assert response.json()["darkPrimary"] == "#445566"
    # an admin change must be visible right away, so the response may not be cached for days
    assert response.headers["Cache-Control"] == "no-cache"


def test_admin_update_theme_overwrites_an_existing_override(api_client: TestClient, admin_user: TestUser):
    api_client.put(api_routes.admin_theme, json={"lightPrimary": "#111111"}, headers=admin_user.token)
    response = api_client.put(api_routes.admin_theme, json={"lightPrimary": "#222222"}, headers=admin_user.token)

    data = response.json()
    assert data["theme"]["lightPrimary"] == "#222222"
    assert data["overridden"] == ["lightPrimary"]


@pytest.mark.parametrize("cleared", [None, ""], ids=["null", "empty string"])
def test_admin_update_theme_clears_a_single_override(api_client: TestClient, admin_user: TestUser, cleared):
    api_client.put(
        api_routes.admin_theme,
        json={"darkAccent": "#123456", "darkError": "#654321"},
        headers=admin_user.token,
    )

    response = api_client.put(api_routes.admin_theme, json={"darkAccent": cleared}, headers=admin_user.token)

    data = response.json()
    assert data["overridden"] == ["darkError"]
    assert data["theme"]["darkAccent"] == data["defaults"]["darkAccent"]
    assert data["theme"]["darkError"] == "#654321"


def test_admin_reset_theme_removes_all_overrides(api_client: TestClient, admin_user: TestUser):
    api_client.put(
        api_routes.admin_theme,
        json={"lightPrimary": "#111111", "darkSurface": "#222222"},
        headers=admin_user.token,
    )

    response = api_client.delete(api_routes.admin_theme, headers=admin_user.token)
    assert response.status_code == 200
    assert response.json()["overridden"] == []

    public = api_client.get(api_routes.app_about_theme).json()
    assert public["lightPrimary"] == get_app_settings().theme.light_primary


@pytest.mark.parametrize("bad_color", ["red", "#fff", "123456", "#12345G", "#1234567", "rgb(0,0,0)"])
def test_admin_update_theme_rejects_invalid_colors(api_client: TestClient, admin_user: TestUser, bad_color: str):
    response = api_client.put(api_routes.admin_theme, json={"darkPrimary": bad_color}, headers=admin_user.token)
    assert response.status_code == 422

    # a rejected request must not change anything
    assert api_client.get(api_routes.admin_theme, headers=admin_user.token).json()["overridden"] == []


def test_admin_update_theme_ignores_unknown_fields(api_client: TestClient, admin_user: TestUser):
    response = api_client.put(api_routes.admin_theme, json={"notAColor": "#112233"}, headers=admin_user.token)
    assert response.status_code == 200
    assert response.json()["overridden"] == []
