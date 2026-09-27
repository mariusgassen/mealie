import { useAdminApi, useUserApi } from "~/composables/api";
import type { AIPromptOverrideUpdate } from "~/lib/api/types/group";

/**
 * When `groupId` is provided, prompts are managed via the admin API for that group
 * (used from the admin group-management page); otherwise the caller's own group is used.
 */
export function useAIPrompts(groupId?: string) {
  const userApi = useUserApi();
  const adminApi = useAdminApi();
  const loading = ref(false);

  async function getAll() {
    loading.value = true;
    try {
      return groupId ? await adminApi.aiPrompts.getAll(groupId) : await userApi.aiPrompts.getAll();
    }
    finally {
      loading.value = false;
    }
  }

  async function updateOne(name: string, payload: AIPromptOverrideUpdate) {
    loading.value = true;
    try {
      return groupId
        ? await adminApi.aiPrompts.updateOne(groupId, name, payload)
        : await userApi.aiPrompts.updateOne(name, payload);
    }
    finally {
      loading.value = false;
    }
  }

  async function resetOne(name: string) {
    loading.value = true;
    try {
      return groupId ? await adminApi.aiPrompts.resetOne(groupId, name) : await userApi.aiPrompts.resetOne(name);
    }
    finally {
      loading.value = false;
    }
  }

  return {
    loading: readonly(loading),
    getAll,
    updateOne,
    resetOne,
  };
}
