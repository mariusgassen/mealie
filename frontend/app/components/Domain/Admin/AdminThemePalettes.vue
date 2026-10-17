<template>
  <div class="theme-palettes">
    <BaseDialog
      v-model="saveDialog"
      bottom-sheet
      :icon="$globals.icons.formatColorFill"
      :title="$t('admin.theme.save-preset')"
      can-submit
      :submit-text="$t('general.save')"
      :submit-disabled="!presetName.trim()"
      @submit="savePreset"
    >
      <v-card-text>
        <v-text-field
          v-model="presetName"
          :label="$t('admin.theme.preset-name')"
          :hint="$t('admin.theme.preset-name-hint')"
          maxlength="60"
          autofocus
          @keydown.enter.prevent="savePreset"
        />
      </v-card-text>
    </BaseDialog>

    <BaseDialog
      v-model="deleteDialog"
      bottom-sheet
      color="error"
      :icon="$globals.icons.alertCircle"
      :title="$t('admin.theme.delete-preset')"
      can-confirm
      @confirm="deletePreset"
    >
      <v-card-text>
        {{ $t("admin.theme.delete-preset-description", { name: toDelete?.name ?? "" }) }}
      </v-card-text>
    </BaseDialog>

    <section class="mb-4">
      <h3 class="theme-palettes__heading">
        {{ $t("admin.theme.presets") }}
      </h3>
      <div class="d-flex align-center flex-wrap ga-2">
        <v-chip
          v-for="preset in builtIn"
          :key="preset"
          :prepend-icon="$globals.icons.formatColorFill"
          variant="tonal"
          @click="emit('apply', applyThemePreset({}, preset))"
        >
          {{ $t(`admin.theme.preset-${preset}`) }}
        </v-chip>
        <v-chip
          v-for="preset in presets"
          :key="preset.id"
          :prepend-icon="$globals.icons.formatColorFill"
          variant="tonal"
          color="primary"
          closable
          :close-label="$t('admin.theme.delete-preset')"
          @click="emit('apply', definedColors(preset.colors))"
          @click:close="askDelete(preset)"
        >
          {{ preset.name }}
        </v-chip>
        <v-btn
          size="small"
          variant="text"
          :prepend-icon="$globals.icons.save"
          @click="openSave"
        >
          {{ $t("admin.theme.save-preset") }}
        </v-btn>
      </div>
    </section>

    <section class="mb-4">
      <h3 class="theme-palettes__heading">
        {{ $t("admin.theme.generator") }}
      </h3>
      <v-chip-group
        v-model="style"
        mandatory
        selected-class="text-primary"
        class="mb-2"
      >
        <v-chip
          v-for="option in THEME_STYLES"
          :key="option"
          :value="option"
          filter
          variant="tonal"
        >
          {{ $t(`admin.theme.style-${option}`) }}
        </v-chip>
      </v-chip-group>
      <div class="d-flex flex-wrap ga-2">
        <v-btn
          variant="tonal"
          color="primary"
          rounded
          :prepend-icon="$globals.icons.refresh"
          @click="shuffle"
        >
          {{ $t("admin.theme.shuffle") }}
        </v-btn>
        <v-btn
          variant="tonal"
          rounded
          :prepend-icon="$globals.icons.formatColorFill"
          @click="fromMainColor"
        >
          {{ $t("admin.theme.from-main-color") }}
        </v-btn>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { useAdminApi } from "~/composables/api";
import { applyThemePreset, themeKey, THEME_COLORS, THEME_MODES, THEME_PRESETS, type ThemeMode } from "~/composables/use-theme-editor";
import { generateTheme, THEME_STYLES, type GeneratedTheme, type ThemeStyle } from "~/composables/use-theme-generator";
import { alert } from "~/composables/use-toast";
import { useGlobalI18n } from "~/composables/use-global-i18n";
import type { AppTheme, AppThemeUpdate, ThemePresetOut } from "~/lib/api/types/admin";

const props = defineProps<{
  /** The palette being edited, including unsaved changes */
  draft: AppTheme;
  /** The mode the admin is looking at; its main color is the starting point for "From main color" */
  mode: ThemeMode;
}>();

// colors to merge into the draft; the page decides what to do with them
const emit = defineEmits<{ apply: [colors: AppTheme] }>();

const i18n = useGlobalI18n();
const adminApi = useAdminApi();

const builtIn = Object.keys(THEME_PRESETS);
const presets = ref<ThemePresetOut[]>([]);
const style = ref<ThemeStyle>("pastel");

const saveDialog = ref(false);
const presetName = ref("");
const deleteDialog = ref(false);
const toDelete = ref<ThemePresetOut | null>(null);

async function loadPresets() {
  const { data } = await adminApi.theme.listPresets();
  presets.value = data ?? [];
}

onMounted(loadPresets);

function toAppTheme(theme: GeneratedTheme): AppTheme {
  const result: Record<string, string> = {};
  for (const mode of THEME_MODES) {
    for (const color of THEME_COLORS) {
      result[themeKey(mode, color)] = theme[mode][color];
    }
  }
  return result as AppTheme;
}

function definedColors(colors: AppThemeUpdate): AppTheme {
  return Object.fromEntries(Object.entries(colors).filter(([, value]) => !!value)) as AppTheme;
}

function shuffle() {
  emit("apply", toAppTheme(generateTheme({ style: style.value })));
}

function fromMainColor() {
  const baseColor = props.draft[themeKey(props.mode, "primary")] ?? undefined;
  emit("apply", toAppTheme(generateTheme({ style: style.value, baseColor })));
}

function openSave() {
  presetName.value = "";
  saveDialog.value = true;
}

async function savePreset() {
  const name = presetName.value.trim();
  if (!name) {
    return;
  }

  const colors: Record<string, string> = {};
  for (const mode of THEME_MODES) {
    for (const color of THEME_COLORS) {
      const value = props.draft[themeKey(mode, color)];
      if (value) {
        colors[themeKey(mode, color)] = value;
      }
    }
  }

  const { data } = await adminApi.theme.savePreset({ name, colors: colors as AppThemeUpdate });
  saveDialog.value = false;
  if (data) {
    await loadPresets();
    alert.success(i18n.t("admin.theme.preset-saved", { name: data.name }));
  }
}

function askDelete(preset: ThemePresetOut) {
  toDelete.value = preset;
  deleteDialog.value = true;
}

async function deletePreset() {
  if (!toDelete.value) {
    return;
  }

  await adminApi.theme.deletePreset(toDelete.value.id);
  deleteDialog.value = false;
  toDelete.value = null;
  await loadPresets();
  alert.success(i18n.t("admin.theme.preset-deleted"));
}
</script>

<style scoped>
.theme-palettes__heading {
  margin-bottom: 8px;
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  opacity: 0.6;
}
</style>
