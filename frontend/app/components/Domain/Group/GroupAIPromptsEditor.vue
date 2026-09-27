<template>
  <div>
    <BaseCardSectionTitle :title="$t('group.ai-prompt-settings.ai-prompt-settings')" size="medium" class="pt-2" />
    <v-card-text class="pt-0 pb-6 px-0">
      {{ $t("group.ai-prompt-settings.ai-prompt-settings-description") }}
    </v-card-text>

    <AppLoader v-if="loading && !prompts.length" />

    <v-card
      v-for="p in prompts"
      :key="p.name"
      variant="tonal"
      class="pa-0 mb-4"
    >
      <v-row no-gutters align="center">
        <v-col :cols="10">
          <v-card-text class="d-flex align-center">
            <span>{{ p.name }}</span>
            <v-chip v-if="p.isOverridden" size="small" color="info" class="ms-2">
              {{ $t('group.ai-prompt-settings.overridden') }}
            </v-chip>
          </v-card-text>
        </v-col>

        <v-col :cols="2">
          <BaseButtonGroup
            :buttons="[
              {
                icon: $globals.icons.edit,
                text: $t('general.edit'),
                event: 'edit',
              },
            ]"
            @edit="openEdit(p)"
          />
        </v-col>
      </v-row>
    </v-card>

    <GroupAIPromptDialog
      v-model="dialogOpen"
      :prompt="editingPrompt"
      @save="handleSave"
      @reset="handleReset"
    />
  </div>
</template>

<script setup lang="ts">
import { useAIPrompts } from "~/composables/use-ai-prompts";
import { alert } from "~/composables/use-toast";
import type { AIPromptOut } from "~/lib/api/types/group";

const i18n = useI18n();
const { loading, getAll, updateOne, resetOne } = useAIPrompts();

const prompts = ref<AIPromptOut[]>([]);
const dialogOpen = ref(false);
const editingPrompt = ref<AIPromptOut | null>(null);

async function refresh() {
  const { data } = await getAll();
  if (data) {
    prompts.value = data;
  }
}

onMounted(() => {
  refresh();
});

function openEdit(prompt: AIPromptOut) {
  editingPrompt.value = prompt;
  dialogOpen.value = true;
}

async function handleSave(content: string) {
  const name = editingPrompt.value?.name;
  if (!name) return;

  const { data } = await updateOne(name, { prompt: content });
  if (data) {
    await refresh();
    dialogOpen.value = false;
    alert.success(i18n.t("group.ai-prompt-settings.prompt-updated"));
  }
  else {
    alert.error(i18n.t("group.ai-prompt-settings.prompt-update-failed"));
  }
}

async function handleReset() {
  const name = editingPrompt.value?.name;
  if (!name) return;

  const { data } = await resetOne(name);
  if (data) {
    await refresh();
    dialogOpen.value = false;
    alert.success(i18n.t("group.ai-prompt-settings.prompt-reset"));
  }
  else {
    alert.error(i18n.t("group.ai-prompt-settings.prompt-reset-failed"));
  }
}
</script>
