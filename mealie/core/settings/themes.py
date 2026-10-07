from pydantic_settings import BaseSettings, SettingsConfigDict


class Theme(BaseSettings):
    light_primary: str = "#E58325"
    light_accent: str = "#007A99"
    light_secondary: str = "#973542"
    light_success: str = "#43A047"
    light_info: str = "#1976D2"
    light_warning: str = "#FF6D00"
    light_error: str = "#EF5350"
    light_background: str = "#F2F2F7"
    light_surface: str = "#FFFFFF"

    dark_primary: str = "#E58325"
    dark_accent: str = "#40C8E0"
    dark_secondary: str = "#E0657A"
    dark_success: str = "#30D158"
    dark_info: str = "#0A84FF"
    dark_warning: str = "#FFB340"
    dark_error: str = "#FF6961"
    dark_background: str = "#1C1C1E"
    dark_surface: str = "#2C2C2E"
    model_config = SettingsConfigDict(env_prefix="theme_", extra="allow")
