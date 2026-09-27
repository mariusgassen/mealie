import { useUserApi } from "~/composables/api";
import type { AIPromptOverrideUpdate } from "~/lib/api/types/group";

export function useAIPrompts() {
  const api = useUserApi();
  const loading = ref(false);

  async function getAll() {
    loading.value = true;
    try {
      return await api.aiPrompts.getAll();
    }
    finally {
      loading.value = false;
    }
  }

  async function updateOne(name: string, payload: AIPromptOverrideUpdate) {
    loading.value = true;
    try {
      return await api.aiPrompts.updateOne(name, payload);
    }
    finally {
      loading.value = false;
    }
  }

  async function resetOne(name: string) {
    loading.value = true;
    try {
      return await api.aiPrompts.resetOne(name);
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
