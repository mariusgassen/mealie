from fastapi import APIRouter, HTTPException, status
from pydantic import UUID4

from mealie.routes._base import BaseAdminController, controller
from mealie.schema.admin.theme import AdminThemeOut, AppThemeUpdate, ThemePresetCreate, ThemePresetOut
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

    @router.get("/presets", response_model=list[ThemePresetOut])
    def get_presets(self):
        """List the palettes admins have saved, by name"""
        return self.service.presets()

    @router.post("/presets", response_model=ThemePresetOut, status_code=status.HTTP_201_CREATED)
    def save_preset(self, data: ThemePresetCreate):
        """Save a palette under a name; an existing preset with that name is replaced"""
        return self.service.save_preset(data)

    @router.delete("/presets/{preset_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_preset(self, preset_id: UUID4):
        """Delete a saved palette"""
        if not self.service.delete_preset(preset_id):
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Theme preset not found")
