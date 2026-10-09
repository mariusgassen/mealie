from fastapi import APIRouter

from mealie.routes._base import BaseAdminController, controller
from mealie.schema.admin.theme import AdminThemeOut, AppThemeUpdate
from mealie.services.app_theme import AppThemeService

router = APIRouter(prefix="/theme")


@controller(router)
class AdminThemeController(BaseAdminController):
    @property
    def service(self) -> AppThemeService:
        return AppThemeService(self.repos)

    @router.get("", response_model=AdminThemeOut)
    def get_theme(self):
        """Get the server theme in effect, the defaults behind it, and which values an admin has overridden"""
        return self.service.admin_view()

    @router.put("", response_model=AdminThemeOut)
    def update_theme(self, data: AppThemeUpdate):
        """Set or clear individual theme colors for the whole server; only the fields sent are changed"""
        return self.service.update(data)

    @router.delete("", response_model=AdminThemeOut)
    def reset_theme(self):
        """Remove every admin override so the theme falls back to the environment variables / defaults"""
        return self.service.reset()
