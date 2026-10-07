from mealie.schema._mealie import MealieModel


class AppStatistics(MealieModel):
    total_recipes: int
    total_users: int
    total_households: int
    total_groups: int
    uncategorized_recipes: int
    untagged_recipes: int


class AppInfo(MealieModel):
    production: bool
    version: str
    demo_status: bool
    allow_signup: bool
    allow_password_login: bool
    default_group_slug: str | None = None
    default_household_slug: str | None = None
    enable_oidc: bool
    oidc_redirect: bool
    oidc_provider_name: str
    token_time: int
    allowed_iframe_hosts: list[str] = []


class AppTheme(MealieModel):
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


class AppStartupInfo(MealieModel):
    is_first_login: bool
    """
    The applications best guess that a user hasn't logged in. Currently, it really
    on indicates that the 'changeme@example.com' user is still in the database. Once
    it is removed, this will always return False.
    """

    is_demo: bool


class AdminAboutInfo(AppInfo):
    versionLatest: str
    api_port: int
    api_docs: bool
    db_type: str
    db_url: str | None = None
    default_group: str
    default_household: str
    build_id: str
    recipe_scraper_version: str


class CheckAppConfig(MealieModel):
    email_ready: bool
    ldap_ready: bool
    ldap_disabled: bool
    oidc_ready: bool
    oidc_disabled: bool
    base_url_set: bool
    is_up_to_date: bool
