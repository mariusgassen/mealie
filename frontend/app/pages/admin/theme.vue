<template>
  <v-container
    fluid
    class="narrow-container theme-page"
  >
    <BasePageTitle divider>
      <template #title>
        {{ $t("admin.theme.title") }}
      </template>
      {{ $t("admin.theme.description") }}
    </BasePageTitle>

    <BaseDialog
      v-model="resetDialog"
      bottom-sheet
      color="warning"
      :icon="$globals.icons.alertCircle"
      :title="$t('admin.theme.reset-all-title')"
      can-confirm
      @confirm="resetAll"
    >
      <v-card-text>
        {{ $t("admin.theme.reset-all-description") }}
      </v-card-text>
    </BaseDialog>

    <template v-if="draft && saved">
      <v-btn-toggle
        v-model="mode"
        mandatory
        class="mb-4"
      >
        <v-btn value="light">
          {{ $t("admin.theme.mode-light") }}
        </v-btn>
        <v-btn value="dark">
          {{ $t("admin.theme.mode-dark") }}
        </v-btn>
      </v-btn-toggle>

      <!-- What the chosen palette looks like, independent of the mode the admin is currently viewing -->
      <div
        class="theme-preview mb-4"
        :style="{ background: colorOf('background'), color: readableTextColor(colorOf('background')) }"
      >
        <div
          class="theme-preview__card"
          :style="{ background: colorOf('surface'), color: readableTextColor(colorOf('surface')) }"
        >
          <div class="theme-preview__title">
            {{ $t("admin.theme.preview") }}
          </div>
          <div class="d-flex flex-wrap ga-2">
            <span
              v-for="color in previewColors"
              :key="color"
              class="theme-preview__chip"
              :style="{ background: colorOf(color), color: readableTextColor(colorOf(color)) }"
            >
              {{ $t(`admin.theme.color-${color}`) }}
            </span>
          </div>
        </div>
      </div>

      <v-card
        flat
        class="mb-4"
      >
        <v-list lines="two">
          <template
            v-for="(color, index) in THEME_COLORS"
            :key="color"
          >
            <v-divider
              v-if="index > 0"
              class="mx-4"
            />
            <v-list-item>
              <template #prepend>
                <v-menu :close-on-content-click="false">
                  <template #activator="{ props: menuProps }">
                    <button
                      v-bind="menuProps"
                      type="button"
                      class="theme-swatch mr-4"
                      :style="{ background: colorOf(color) }"
                      :aria-label="$t(`admin.theme.color-${color}`)"
                    />
                  </template>
                  <v-color-picker
                    :model-value="colorOf(color)"
                    mode="hex"
                    :modes="['hex']"
                    hide-inputs
                    @update:model-value="setColor(color, $event)"
                  />
                </v-menu>
              </template>

              <v-list-item-title class="d-flex align-center flex-wrap ga-2 text-wrap">
                {{ $t(`admin.theme.color-${color}`) }}
                <v-chip
                  v-if="isOverridden(color)"
                  size="x-small"
                  color="primary"
                  variant="tonal"
                >
                  {{ $t("admin.theme.customized") }}
                </v-chip>
              </v-list-item-title>
              <v-list-item-subtitle class="text-wrap">
                <span class="theme-hint">{{ $t(`admin.theme.color-${color}-hint`) }} · </span>
                {{ $t("admin.theme.default-value", { value: defaultOf(color) }) }}
              </v-list-item-subtitle>

              <template #append>
                <v-text-field
                  :model-value="typed[themeKey(mode, color)] ?? colorOf(color)"
                  density="compact"
                  hide-details="auto"
                  maxlength="7"
                  class="theme-hex-input"
                  :error="typed[themeKey(mode, color)] !== undefined"
                  :error-messages="typed[themeKey(mode, color)] !== undefined ? $t('admin.theme.invalid-color') : undefined"
                  @update:model-value="typeColor(color, $event)"
                  @blur="typed[themeKey(mode, color)] = undefined"
                />
                <v-btn
                  icon
                  variant="text"
                  size="small"
                  class="ml-1"
                  :disabled="colorOf(color) === defaultOf(color)"
                  :class="{ 'theme-reset--idle': colorOf(color) === defaultOf(color) }"
                  :aria-label="$t('admin.theme.reset-color')"
                  @click="setColor(color, defaultOf(color))"
                >
                  <v-icon>{{ $globals.icons.undo }}</v-icon>
                  <v-tooltip
                    activator="parent"
                    location="top"
                  >
                    {{ $t("admin.theme.reset-color") }}
                  </v-tooltip>
                </v-btn>
              </template>
            </v-list-item>
          </template>
        </v-list>
      </v-card>

      <div class="d-flex justify-end">
        <v-btn
          variant="text"
          color="error"
          :disabled="saved.overridden.length === 0 && !isDirty"
          @click="resetDialog = true"
        >
          {{ $t("admin.theme.reset-all") }}
        </v-btn>
      </div>

      <!-- Save bar, only while there is something to save -->
      <Transition name="theme-bar">
        <div
          v-if="isDirty"
          class="theme-actions d-print-none"
        >
          <span class="theme-actions__label">{{ $t("admin.theme.unsaved-changes") }}</span>
          <v-spacer />
          <v-btn
            variant="text"
            @click="discard"
          >
            {{ $t("admin.theme.discard") }}
          </v-btn>
          <v-btn
            color="primary"
            :loading="saving"
            @click="save"
          >
            {{ $t("general.save") }}
          </v-btn>
        </div>
      </Transition>
    </template>
  </v-container>
</template>

<script setup lang="ts">
import { useTheme } from "vuetify";
import { useAdminApi } from "~/composables/api";
import {
  buildThemeUpdate,
  isHexColor,
  normalizeHexColor,
  readableTextColor,
  themeKey,
  THEME_COLORS,
  THEME_MODES,
  type ThemeColor,
  type ThemeMode,
} from "~/composables/use-theme-editor";
import { alert } from "~/composables/use-toast";
import { useGlobalI18n } from "~/composables/use-global-i18n";
import type { AdminThemeOut, AppTheme } from "~/lib/api/types/admin";

definePageMeta({
  layout: "admin",
});

const i18n = useGlobalI18n();
const adminApi = useAdminApi();
const vuetifyTheme = useTheme();

const previewColors: ThemeColor[] = ["primary", "accent", "secondary", "success", "info", "warning", "error"];

// the palette being edited: light or dark; starts on whichever one is currently showing
const mode = ref<ThemeMode>(vuetifyTheme.current.value.dark ? "dark" : "light");

// what the server has now (effective theme, the defaults behind it, which values are overridden)
const saved = ref<AdminThemeOut | null>(null);
// the working copy the admin is editing
const draft = ref<AppTheme | null>(null);
// text typed into a hex field that is not (yet) a valid color
const typed = reactive<Record<string, string | undefined>>({});
const saving = ref(false);
const resetDialog = ref(false);

function colorOf(color: ThemeColor): string {
  return draft.value?.[themeKey(mode.value, color)] ?? "#000000";
}

function defaultOf(color: ThemeColor): string {
  return saved.value?.defaults[themeKey(mode.value, color)] ?? "";
}

function isOverridden(color: ThemeColor): boolean {
  return colorOf(color) !== defaultOf(color);
}

function setColor(color: ThemeColor, value: string) {
  const normalized = normalizeHexColor(value);
  if (!normalized || !draft.value) {
    return;
  }
  const key = themeKey(mode.value, color);
  typed[key] = undefined;
  draft.value[key] = normalized;
}

function typeColor(color: ThemeColor, value: string) {
  const key = themeKey(mode.value, color);
  if (normalizeHexColor(value)) {
    setColor(color, value);
  }
  else {
    typed[key] = value;
  }
}

const isDirty = computed(() => {
  if (!draft.value || !saved.value) {
    return false;
  }
  return Object.keys(buildThemeUpdate(draft.value, saved.value.theme, saved.value.defaults)).length > 0;
});

// Show the edited colors on the real app right away, in whichever mode is active, until saved or discarded
function applyToApp(theme: AppTheme) {
  for (const themeMode of THEME_MODES) {
    const colors = vuetifyTheme.themes.value[themeMode]?.colors;
    if (!colors) {
      continue;
    }
    for (const color of THEME_COLORS) {
      const value = theme[themeKey(themeMode, color)];
      if (isHexColor(value)) {
        colors[color] = value;
      }
    }
  }
}

watch(draft, (theme) => {
  if (theme) {
    applyToApp(theme);
  }
}, { deep: true });

function load(data: AdminThemeOut) {
  saved.value = data;
  draft.value = { ...data.theme };
  Object.keys(typed).forEach((key) => {
    typed[key] = undefined;
  });
}

onMounted(async () => {
  const { data } = await adminApi.theme.get();
  if (data) {
    load(data);
  }
});

async function save() {
  if (!draft.value || !saved.value) {
    return;
  }
  saving.value = true;
  const payload = buildThemeUpdate(draft.value, saved.value.theme, saved.value.defaults);
  const { data } = await adminApi.theme.update(payload);
  saving.value = false;

  if (data) {
    load(data);
    alert.success(i18n.t("admin.theme.saved"));
  }
}

function discard() {
  if (saved.value) {
    load(saved.value);
    applyToApp(saved.value.theme);
  }
}

async function resetAll() {
  const { data } = await adminApi.theme.reset();
  if (data) {
    load(data);
    applyToApp(data.theme);
    alert.success(i18n.t("admin.theme.reset-done"));
  }
}

// leaving with unsaved edits must not leave their colors applied to the rest of the app
onBeforeUnmount(() => {
  if (isDirty.value && saved.value) {
    applyToApp(saved.value.theme);
  }
});
</script>

<style scoped>
/* room below the list for the floating save bar */
.theme-page {
  padding-bottom: 120px;
}

/* let hints and defaults wrap instead of being cut off with an ellipsis */
.theme-page :deep(.v-list-item-subtitle) {
  white-space: normal;
  -webkit-line-clamp: unset;
  line-clamp: unset;
}

@media (max-width: 599px) {
  .theme-hex-input {
    width: 7rem;
  }

  /* the descriptive hint is a luxury on a phone; the default value stays */
  .theme-hint {
    display: none;
  }

  /* nothing to reset: give the width back to the text */
  .theme-reset--idle {
    display: none;
  }

  /* the bar itself says there is something to save; on a phone the buttons need the room */
  .theme-actions__label {
    display: none;
  }

  .theme-actions {
    padding-left: 8px;
  }

  .theme-actions .v-btn {
    flex: 1;
  }
}

.theme-preview {
  border-radius: 16px;
  padding: 16px;
  border: 0.5px solid var(--mealie-ios-separator);
}

.theme-preview__card {
  border-radius: 12px;
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  border: 0.5px solid var(--mealie-ios-separator);
}

.theme-preview__title {
  font-weight: 600;
}

.theme-preview__chip {
  border-radius: 999px;
  padding: 4px 12px;
  font-size: 0.8125rem;
  font-weight: 600;
}

.theme-swatch {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: 0.5px solid var(--mealie-ios-separator);
  box-shadow: inset 0 0 0 2px rgba(255, 255, 255, 0.35);
  cursor: pointer;
}

.theme-hex-input {
  width: 8.5rem;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
}

.theme-actions {
  position: fixed;
  left: 50%;
  transform: translateX(-50%);
  bottom: calc(var(--mealie-bottom-nav-height, 0px) + env(safe-area-inset-bottom) + 16px);
  z-index: 2010;
  display: flex;
  align-items: center;
  gap: 8px;
  width: min(36rem, calc(100vw - 24px));
  padding: 8px 8px 8px 16px;
  border-radius: 18px;
  background: rgba(var(--v-theme-surface), 0.85);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  box-shadow: 0 8px 28px rgba(0, 0, 0, 0.22);
  border: 0.5px solid var(--mealie-ios-separator);
}

.theme-actions__label {
  font-size: 0.875rem;
  opacity: 0.75;
}

.theme-bar-enter-active,
.theme-bar-leave-active {
  transition:
    opacity 0.2s ease,
    transform 0.3s var(--mealie-ios-spring);
}

.theme-bar-enter-from,
.theme-bar-leave-to {
  opacity: 0;
  transform: translate(-50%, 16px);
}
</style>
