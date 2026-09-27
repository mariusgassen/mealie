import { BaseAPI } from "../base/base-clients";
import type { AIPromptOut, AIPromptOverrideUpdate } from "~/lib/api/types/group";

const prefix = "/api/admin";

const routes = {
  prompts: (groupId: string) => `${prefix}/groups/${groupId}/ai-providers/prompts`,
  promptsName: (groupId: string, name: string) =>
    `${prefix}/groups/${groupId}/ai-providers/prompts/${encodeURIComponent(name)}`,
};

export class AdminAIPromptsApi extends BaseAPI {
  async getAll(groupId: string) {
    return await this.requests.get<AIPromptOut[]>(routes.prompts(groupId));
  }

  async getOne(groupId: string, name: string) {
    return await this.requests.get<AIPromptOut>(routes.promptsName(groupId, name));
  }

  async updateOne(groupId: string, name: string, payload: AIPromptOverrideUpdate) {
    return await this.requests.put<AIPromptOut, AIPromptOverrideUpdate>(routes.promptsName(groupId, name), payload);
  }

  async resetOne(groupId: string, name: string) {
    return await this.requests.delete<AIPromptOut>(routes.promptsName(groupId, name));
  }
}
