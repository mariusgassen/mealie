import { BaseAPI } from "../base/base-clients";
import type { AdminThemeOut, AppThemeUpdate } from "~/lib/api/types/admin";

const prefix = "/api";

const routes = {
  theme: `${prefix}/admin/theme`,
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
}
