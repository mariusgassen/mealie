from pydantic import UUID4
from pydantic.alias_generators import to_camel

from mealie.repos.repository_factory import AllRepositories
from mealie.schema.admin.about import AppTheme
from mealie.schema.admin.theme import AdminThemeOut, AppThemeUpdate, ThemePresetCreate, ThemePresetOut
from mealie.services._base_service import BaseService


class AppThemeService(BaseService):
    """
    Resolves the server-wide theme. Precedence, highest first:

    1. values an admin saved in the database (`server_theme_overrides`)
    2. the `THEME_*` environment variables
    3. the built-in defaults
    """

    def __init__(self, repos: AllRepositories) -> None:
        super().__init__()
        self.repos = repos

    def defaults(self) -> AppTheme:
        """The theme without any admin override: environment variables on top of the built-in defaults"""
        return AppTheme(**self.settings.theme.model_dump())

    def overrides(self) -> dict[str, str]:
        known = set(AppTheme.model_fields)
        return {row.key: row.value for row in self.repos.server_theme_overrides.get_all() if row.key in known}

    def effective(self) -> AppTheme:
        return AppTheme(**{**self.defaults().model_dump(), **self.overrides()})

    def admin_view(self) -> AdminThemeOut:
        return AdminThemeOut(
            theme=self.effective(),
            defaults=self.defaults(),
            overridden=sorted(to_camel(key) for key in self.overrides()),
        )

    def update(self, data: AppThemeUpdate) -> AdminThemeOut:
        existing = {row.key: row for row in self.repos.server_theme_overrides.get_all()}

        for key, value in data.model_dump(exclude_unset=True).items():
            row = existing.get(key)

            if not value:
                if row:
                    self.repos.server_theme_overrides.delete(row.id)
            elif row:
                self.repos.server_theme_overrides.update(row.id, {"value": value})
            else:
                self.repos.server_theme_overrides.create({"key": key, "value": value})

        return self.admin_view()

    def reset(self) -> AdminThemeOut:
        # not delete_all(): RepositoryGeneric.delete_all builds its DELETE but never executes it
        self.repos.server_theme_overrides.delete_many([row.id for row in self.repos.server_theme_overrides.get_all()])
        return self.admin_view()

    def presets(self) -> list[ThemePresetOut]:
        return sorted(self.repos.server_theme_presets.get_all(), key=lambda preset: preset.name.lower())

    def save_preset(self, data: ThemePresetCreate) -> ThemePresetOut:
        colors = data.colors.model_dump(exclude_none=True)
        existing = next((row for row in self.repos.server_theme_presets.get_all() if row.name == data.name), None)

        if existing:
            return self.repos.server_theme_presets.update(existing.id, {"name": data.name, "colors": colors})

        return self.repos.server_theme_presets.create({"name": data.name, "colors": colors})

    def delete_preset(self, preset_id: UUID4) -> bool:
        if not self.repos.server_theme_presets.get_one(preset_id):
            return False

        self.repos.server_theme_presets.delete(preset_id)
        return True
