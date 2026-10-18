"""
The app icon / favicon and the web manifest follow the server theme.
"""

import io
import json
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from mealie.routes.spa.manifest import serve_manifest
from tests.utils import api_routes
from tests.utils.fixture_schemas import TestUser

PRIMARY = "#2F8F7A"


@pytest.fixture(autouse=True)
def reset_theme(api_client: TestClient, admin_user: TestUser) -> Generator[None]:
    api_client.delete(api_routes.admin_theme, headers=admin_user.token)
    yield
    api_client.delete(api_routes.admin_theme, headers=admin_user.token)


def _set_primary(api_client: TestClient, admin_user: TestUser, color: str) -> None:
    response = api_client.put(api_routes.admin_theme, json={"lightPrimary": color}, headers=admin_user.token)
    assert response.status_code == 200


def _close(pixel: tuple[int, ...], color: str, tolerance: int = 60) -> bool:
    expected = tuple(int(color[i : i + 2], 16) for i in (1, 3, 5))
    return all(abs(a - b) <= tolerance for a, b in zip(pixel[:3], expected, strict=True))


def test_icon_is_public_png_in_the_requested_size(api_client: TestClient):
    response = api_client.get(api_routes.app_about_icons_name("android-chrome-192x192.png"))
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"

    image = Image.open(io.BytesIO(response.content))
    assert image.size == (192, 192)


def test_icon_uses_the_theme_primary_color(api_client: TestClient, admin_user: TestUser):
    _set_primary(api_client, admin_user, PRIMARY)

    response = api_client.get(api_routes.app_about_icons_name("apple-touch-icon.png"))
    image = Image.open(io.BytesIO(response.content)).convert("RGBA")

    # full-bleed icons have no transparency, and the corner (no glyph) is the tile color
    assert image.size == (180, 180)
    assert image.getpixel((4, 90))[3] == 255
    assert _close(image.getpixel((4, 90)), PRIMARY)


def test_rounded_icons_are_transparent_in_the_corners(api_client: TestClient):
    response = api_client.get(api_routes.app_about_icons_name("android-chrome-512x512.png"))
    image = Image.open(io.BytesIO(response.content)).convert("RGBA")
    assert image.getpixel((0, 0))[3] == 0


def test_icon_changes_with_the_theme_and_supports_etags(api_client: TestClient, admin_user: TestUser):
    name = "favicon-32x32.png"
    first = api_client.get(api_routes.app_about_icons_name(name))
    etag = first.headers["etag"]

    cached = api_client.get(api_routes.app_about_icons_name(name), headers={"If-None-Match": etag})
    assert cached.status_code == 304

    _set_primary(api_client, admin_user, "#112233")
    changed = api_client.get(api_routes.app_about_icons_name(name), headers={"If-None-Match": etag})
    assert changed.status_code == 200
    assert changed.headers["etag"] != etag


def test_favicon_ico(api_client: TestClient):
    response = api_client.get(api_routes.app_about_icons_name("favicon.ico"))
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/x-icon"
    assert response.content[:4] == b"\x00\x00\x01\x00"


def test_unknown_icon_is_404(api_client: TestClient):
    assert api_client.get(api_routes.app_about_icons_name("nope.png")).status_code == 404
    assert api_client.get(api_routes.app_about_icons_name("..%2Fsecret.png")).status_code == 404


def test_manifest_follows_the_theme(api_client: TestClient, admin_user: TestUser):
    _set_primary(api_client, admin_user, PRIMARY)
    api_client.put(api_routes.admin_theme, json={"lightBackground": "#F4F8F6"}, headers=admin_user.token)

    # the route itself only exists when the built frontend is served, so call the handler directly
    manifest = json.loads(serve_manifest(admin_user.repos.session).body)
    assert manifest["theme_color"] == PRIMARY
    assert manifest["background_color"] == "#F4F8F6"
    assert all(icon["src"].startswith("/api/app/about/icons/") for icon in manifest["icons"])
    assert all(icon["src"].endswith(f"?v={PRIMARY.lstrip('#')}") for icon in manifest["icons"])
