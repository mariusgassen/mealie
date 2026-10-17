import { BaseAPI } from "../base/base-clients";
import type { AdminThemeOut, AppThemeUpdate, ThemePresetCreate, ThemePresetOut } from "~/lib/api/types/admin";

const prefix = "/api";

const routes = {
  theme: `${prefix}/admin/theme`,
  presets: `${prefix}/admin/theme/presets`,
  preset: (id: string) => `${prefix}/admin/theme/presets/${id}`,
};

export class AdminThemeAPI extends BaseAPI {
  async get() {
    return await this.requests.get<AdminThemeOut>(routes.theme);
  }

  async update(payload: AppThemeUpdate) {
    return await this.requests.put<AdminThemeOut, AppThemeUpdate>(routes.theme, payload);
  }

  async reset() {
    return await this.requests.delete<AdminThemeOut>(routes.theme);
  }

  async listPresets() {
    return await this.requests.get<ThemePresetOut[]>(routes.presets);
  }

  async savePreset(payload: ThemePresetCreate) {
    return await this.requests.post<ThemePresetOut>(routes.presets, payload);
  }

  async deletePreset(id: string) {
    return await this.requests.delete(routes.preset(id));
  }
}
