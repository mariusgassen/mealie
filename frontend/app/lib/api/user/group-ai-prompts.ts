import { BaseAPI } from "../base/base-clients";
import type { AIPromptOut, AIPromptOverrideUpdate } from "~/lib/api/types/group";

const prefix = "/api/groups/ai-providers";

const routes = {
  prompts: `${prefix}/prompts`,
  promptsName: (name: string) => `${prefix}/prompts/${encodeURIComponent(name)}`,
};

export class AIPromptsAPI extends BaseAPI {
  async getAll() {
    return await this.requests.get<AIPromptOut[]>(routes.prompts);
  }

  async getOne(name: string) {
    return await this.requests.get<AIPromptOut>(routes.promptsName(name));
  }

  async updateOne(name: string, payload: AIPromptOverrideUpdate) {
    return await this.requests.put<AIPromptOut, AIPromptOverrideUpdate>(routes.promptsName(name), payload);
  }

  async resetOne(name: string) {
    return await this.requests.delete<AIPromptOut>(routes.promptsName(name));
  }
}
