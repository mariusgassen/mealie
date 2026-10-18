<template>
  <div>
    <BaseCardSectionTitle :title="$t('group.ai-request-log.title')" size="medium" class="pt-2" />
    <v-card-text class="pt-0 pb-4 px-0">
      {{ $t("group.ai-request-log.description") }}
    </v-card-text>

    <div class="d-flex mb-4 ga-2">
      <v-btn variant="tonal" :loading="loading" :prepend-icon="$globals.icons.refresh" @click="refresh">
        {{ $t("group.ai-request-log.refresh") }}
      </v-btn>
      <v-btn
        variant="text"
        color="warning"
        :disabled="!entries.length"
        :prepend-icon="$globals.icons.delete"
        @click="clear"
      >
        {{ $t("group.ai-request-log.clear") }}
      </v-btn>
    </div>

    <v-card-text v-if="!entries.length && !loading" class="px-0">
      {{ $t("group.ai-request-log.empty") }}
    </v-card-text>

    <v-expansion-panels v-else variant="accordion">
      <v-expansion-panel v-for="(entry, index) in entries" :key="index">
        <v-expansion-panel-title>
          <div class="d-flex flex-column">
            <span>{{ entry.requestType }} · {{ entry.model }}</span>
            <span class="text-caption text-medium-emphasis">{{ formatTimestamp(entry.timestamp) }}</span>
          </div>
          <v-chip v-if="entry.error" size="small" color="error" class="ms-2">
            {{ $t("group.ai-request-log.error") }}
          </v-chip>
        </v-expansion-panel-title>
        <v-expansion-panel-text>
          <div v-if="entry.error" class="mb-4">
            <div class="text-subtitle-2">
              {{ $t("group.ai-request-log.error") }}
            </div>
            <pre class="request-log-text">{{ entry.error }}</pre>
          </div>
          <div class="mb-4">
            <div class="text-subtitle-2">
              {{ $t("group.ai-request-log.system-prompt") }}
            </div>
            <pre class="request-log-text">{{ entry.systemPrompt }}</pre>
          </div>
          <div class="mb-4">
            <div class="text-subtitle-2">
              {{ $t("group.ai-request-log.user-message") }}
            </div>
            <pre class="request-log-text">{{ entry.userMessage }}</pre>
          </div>
          <div v-if="entry.rawResponse">
            <div class="text-subtitle-2">
              {{ $t("group.ai-request-log.raw-response") }}
            </div>
            <pre class="request-log-text">{{ entry.rawResponse }}</pre>
          </div>
        </v-expansion-panel-text>
      </v-expansion-panel>
    </v-expansion-panels>
  </div>
</template>

<script setup lang="ts">
import { useUserApi } from "~/composables/api";
import { alert } from "~/composables/use-toast";
import type { AIRequestLogEntry } from "~/lib/api/types/group";

const i18n = useI18n();
const api = useUserApi();

const entries = ref<AIRequestLogEntry[]>([]);
const loading = ref(false);

async function refresh() {
  loading.value = true;
  try {
    const { data } = await api.aiRequestLog.getAll();
    if (data) {
      entries.value = data;
    }
    else {
      alert.error(i18n.t("group.ai-request-log.failed"));
    }
  }
  finally {
    loading.value = false;
  }
}

async function clear() {
  await api.aiRequestLog.clear();
  await refresh();
}

function formatTimestamp(timestamp: string) {
  return new Date(timestamp).toLocaleString();
}

onMounted(refresh);
</script>

<style scoped>
.request-log-text {
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 0.8rem;
  max-height: 300px;
  overflow: auto;
  padding: 8px;
  border-radius: 4px;
  background: rgba(var(--v-theme-on-surface), 0.05);
}
</style>
