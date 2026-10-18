import { BaseAPI } from "../base/base-clients";
import type { AIRequestLogEntry } from "~/lib/api/types/group";

const routes = {
  requestLog: "/api/groups/ai-providers/request-log",
};

export class AIRequestLogAPI extends BaseAPI {
  async getAll() {
    return await this.requests.get<AIRequestLogEntry[]>(routes.requestLog);
  }

  async clear() {
    return await this.requests.delete<null>(routes.requestLog);
  }
}
