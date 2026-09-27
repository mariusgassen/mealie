<template>
  <BaseDialog
    v-model="dialog"
    :title="$t('group.ai-prompt-settings.edit-prompt')"
    :icon="$globals.icons.robot"
    can-submit
    :submit-icon="$globals.icons.save"
    :submit-text="$t('general.update')"
    :submit-disabled="!formData.trim()"
    width="70%"
    @submit="$emit('save', formData)"
    @close="resetForm"
  >
    <v-card-text v-if="prompt" style="max-height: 70vh; overflow-y: auto;">
      <div class="d-flex align-center mb-2">
        <span class="text-subtitle-2">{{ prompt.name }}</span>
        <v-chip v-if="prompt.isOverridden" size="small" color="info" class="ms-2">
          {{ $t('group.ai-prompt-settings.overridden') }}
        </v-chip>
      </div>
      <v-textarea
        v-model="formData"
        :label="$t('group.ai-prompt-settings.prompt')"
        variant="outlined"
        auto-grow
        rows="10"
      />
    </v-card-text>

    <template #custom-card-action>
      <v-btn
        v-if="prompt?.isOverridden"
        variant="text"
        color="warning"
        @click="confirmReset = true"
      >
        {{ $t('group.ai-prompt-settings.reset-to-default') }}
      </v-btn>
    </template>
  </BaseDialog>

  <BaseDialog
    v-model="confirmReset"
    :title="$t('group.ai-prompt-settings.reset-to-default')"
    color="warning"
    :icon="$globals.icons.undo"
    can-confirm
    @confirm="handleReset"
  >
    <v-card-text>
      {{ $t('group.ai-prompt-settings.reset-to-default-confirm') }}
    </v-card-text>
  </BaseDialog>
</template>

<script setup lang="ts">
import type { AIPromptOut } from "~/lib/api/types/group";

const props = defineProps<{
  prompt: AIPromptOut | null;
}>();

const emit = defineEmits<{
  (e: "save", content: string): void;
  (e: "reset"): void;
}>();

const dialog = defineModel<boolean>({ default: false });

const formData = ref("");
const confirmReset = ref(false);

watch(
  () => [dialog.value, props.prompt] as const,
  ([open, prompt]) => {
    if (open && prompt) {
      formData.value = prompt.content;
    }
  },
  { immediate: true },
);

function resetForm() {
  formData.value = props.prompt?.content ?? "";
}

function handleReset() {
  confirmReset.value = false;
  emit("reset");
}
</script>
