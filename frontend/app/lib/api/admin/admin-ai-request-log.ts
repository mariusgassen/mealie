import { BaseAPI } from "../base/base-clients";
import type { AIRequestLogEntry } from "~/lib/api/types/group";

const routes = {
  requestLog: (groupId: string) => `/api/admin/groups/${groupId}/ai-providers/request-log`,
};

export class AdminAIRequestLogApi extends BaseAPI {
  async getAll(groupId: string) {
    return await this.requests.get<AIRequestLogEntry[]>(routes.requestLog(groupId));
  }

  async clear(groupId: string) {
    return await this.requests.delete<null>(routes.requestLog(groupId));
  }
}
