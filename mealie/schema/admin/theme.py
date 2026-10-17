import re

from pydantic import UUID4, ConfigDict, field_validator

from mealie.schema._mealie import MealieModel

from .about import AppTheme

_HEX_COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")


class AppThemeUpdate(MealieModel):
    """
    A partial update of the server theme. Only the fields that are sent are touched: a color sets
    (or replaces) that value, while `null` or an empty string removes the admin override so the
    value falls back to the environment variable / built-in default.
    """

    light_primary: str | None = None
    light_accent: str | None = None
    light_secondary: str | None = None
    light_success: str | None = None
    light_info: str | None = None
    light_warning: str | None = None
    light_error: str | None = None
    light_background: str | None = None
    light_surface: str | None = None

    dark_primary: str | None = None
    dark_accent: str | None = None
    dark_secondary: str | None = None
    dark_success: str | None = None
    dark_info: str | None = None
    dark_warning: str | None = None
    dark_error: str | None = None
    dark_background: str | None = None
    dark_surface: str | None = None

    @field_validator("*")
    @classmethod
    def validate_hex_color(cls, value: str | None) -> str | None:
        if value is None or value == "":
            return value

        if not _HEX_COLOR.match(value):
            raise ValueError("Colors must be written as #RRGGBB")

        return value.upper()


class AdminThemeOut(MealieModel):
    theme: AppTheme
    """The theme in effect: admin overrides, then environment variables, then built-in defaults"""
    defaults: AppTheme
    """What each value would be without any admin override (environment variables / built-in defaults)"""
    overridden: list[str]
    """The names of the values currently set by an admin, e.g. `darkPrimary`"""


class ServerThemeOverrideOut(MealieModel):
    id: UUID4
    key: str
    value: str

    model_config = ConfigDict(from_attributes=True)


class ThemePresetCreate(MealieModel):
    """Saves a palette under a name; saving an existing name replaces that preset"""

    name: str
    colors: AppThemeUpdate

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if not 1 <= len(value) <= 60:
            raise ValueError("Preset names must be between 1 and 60 characters")

        return value

    @field_validator("colors")
    @classmethod
    def validate_colors(cls, value: AppThemeUpdate) -> AppThemeUpdate:
        if not any(value.model_dump().values()):
            raise ValueError("A preset needs at least one color")

        return value


class ThemePresetOut(MealieModel):
    id: UUID4
    name: str
    colors: AppThemeUpdate

    model_config = ConfigDict(from_attributes=True)
