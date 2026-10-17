<template>
  <div class="editor-bar d-print-none">
    <BaseDialog
      v-model="deleteDialog"
      bottom-sheet
      :title="$t('recipe.delete-recipe')"
      color="error"
      :icon="$globals.icons.alertCircle"
      can-confirm
      @confirm="$emit('delete')"
    >
      <v-card-text>
        {{ $t("recipe.delete-confirmation") }}
      </v-card-text>
    </BaseDialog>

    <v-btn
      variant="text"
      class="editor-bar__cancel"
      @click="$emit('close')"
    >
      {{ $t("general.cancel") }}
    </v-btn>

    <div class="editor-bar__heading">
      <div class="editor-bar__label">
        {{ $t("recipe.edit-recipe") }}
      </div>
      <div class="editor-bar__name">
        {{ name }}
      </div>
    </div>

    <v-menu :location="$vuetify.display.mdAndUp ? 'bottom end' : 'top end'">
      <template #activator="{ props: menuProps }">
        <v-btn
          v-bind="menuProps"
          icon
          variant="text"
          :aria-label="$t('recipe.recipe-actions')"
        >
          <v-icon>{{ $globals.icons.dotsVertical }}</v-icon>
        </v-btn>
      </template>
      <v-list density="comfortable">
        <v-list-item
          :prepend-icon="$globals.icons.codeBraces"
          :title="$t('general.json')"
          @click="$emit('json')"
        />
        <v-divider />
        <v-list-item
          :prepend-icon="$globals.icons.delete"
          :title="$t('general.delete')"
          base-color="error"
          @click="deleteDialog = true"
        />
      </v-list>
    </v-menu>

    <v-btn
      color="primary"
      variant="flat"
      class="editor-bar__save"
      @click="$emit('save')"
    >
      {{ $t("general.save") }}
    </v-btn>
  </div>
</template>

<script setup lang="ts">
import { useEventListener } from "@vueuse/core";

defineProps<{ name?: string | null }>();

const emit = defineEmits<{
  (e: "save" | "close" | "json" | "delete"): void;
}>();

const deleteDialog = ref(false);

// Ctrl/Cmd+S saves, like in any document editor
useEventListener(window, "keydown", (event: KeyboardEvent) => {
  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "s") {
    event.preventDefault();
    emit("save");
  }
});
</script>

<style scoped>
/* iOS-style navigation bar that stays under the app bar while you scroll the form */
.editor-bar {
  position: sticky;
  top: calc(var(--mealie-header-height, 48px) + env(safe-area-inset-top));
  z-index: 5;
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 8px;
  background: rgba(var(--v-theme-background), 0.82);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border-bottom: 0.5px solid var(--mealie-ios-separator);
}

.editor-bar__heading {
  flex: 1;
  min-width: 0;
  text-align: center;
}

.editor-bar__label {
  font-size: 0.75rem;
  opacity: 0.6;
  line-height: 1.1;
}

.editor-bar__name {
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.editor-bar__save {
  font-weight: 600;
}

/* phones: dock the bar above the tab bar so Cancel/Save are within thumb reach */
@media (max-width: 959px) {
  .editor-bar {
    position: fixed;
    top: auto;
    left: 0;
    right: 0;
    bottom: calc(var(--mealie-bottom-nav-height, 0px) + env(safe-area-inset-bottom));
    z-index: 2004;
    padding: 6px 12px;
    border-bottom: 0;
    border-top: 0.5px solid var(--mealie-ios-separator);
  }

  /* the title is already in the page; the space goes to the controls */
  .editor-bar__heading > * {
    display: none;
  }
}

/* the title would be crowded out by three controls on a narrow phone */
@media (max-width: 380px) {
  .editor-bar__label {
    display: none;
  }
}
</style>
