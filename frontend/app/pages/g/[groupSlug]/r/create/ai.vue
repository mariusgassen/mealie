<template>
  <v-form ref="domUrlForm" @submit.prevent="createRecipe">
    <div>
      <v-card-title class="headline">
        {{ $t('recipe.import-with-ai') }}
      </v-card-title>
      <v-card-text v-if="!aiEnabled">
        <v-alert type="info" variant="tonal">
          {{ $t('recipe.import-with-ai-provider-required') }}
        </v-alert>
      </v-card-text>
      <v-card-text v-else>
        <div class="d-flex flex-wrap ga-2 mb-2">
          <v-chip
            v-for="option in sourceOptions"
            :key="option.value"
            :prepend-icon="has(option.value) ? $globals.icons.check : option.icon"
            :color="has(option.value) ? 'primary' : undefined"
            variant="tonal"
            :disabled="state.loading"
            @click="toggleSource(option.value)"
          >
            {{ option.label }}
          </v-chip>
        </div>

        <template v-if="has('url')">
          <v-text-field
            v-model="recipeUrl"
            :label="$t('new-recipe.recipe-url')"
            :prepend-inner-icon="$globals.icons.link"
            validate-on="blur"
            variant="solo-filled"
            clearable
            rounded
            :rules="[validators.urlOptional]"
            :hint="$t('recipe.import-with-ai-url-hint')"
            class="mt-2"
            autofocus
            :disabled="state.loading"
          />

          <BaseHelpText class="mb-4">
            <p>{{ $t('recipe.import-with-ai-description') }}</p>
            <p>
              {{ $t('recipe.import-with-ai-video-description') }}
            </p>
            <p>
              {{ $t('recipe.import-with-ai-without-ai-question') }}
              <router-link :to="urlImporterTarget" class="text-primary">{{ $t('recipe.import-with-ai-use-url-import') }}</router-link>.
            </p>
            <p>
              {{ $t('recipe.scrape-recipe-have-raw-html-or-json-data') }}
              <router-link :to="htmlOrJsonImporterTarget" class="text-primary">{{ $t('recipe.scrape-recipe-you-can-import-from-raw-data-directly') }}</router-link>.
            </p>
          </BaseHelpText>
        </template>

        <template v-if="has('json')">
          <RecipeJsonEditor
            v-model="newRecipeData"
            height="250px"
            mode="code"
            :main-menu-bar="false"
          />
        </template>
        <template v-else-if="has('text')">
          <v-textarea
            v-model="newRecipeData"
            :label="$t('recipe.import-with-ai-content')"
            :prepend-inner-icon="$globals.icons.textBox"
            validate-on="blur"
            variant="solo-filled"
            clearable
            rounded
            :hint="$t('recipe.import-with-ai-content-hint')"
            :disabled="state.loading"
          />
        </template>

        <template v-if="has('images')">
          <div v-if="imagesEnabled" class="mb-4">
            <RecipeImportImages v-model="uploadedImages" :disabled="state.loading" />
          </div>
          <v-alert
            v-else
            type="info"
            variant="tonal"
          >
            {{ $t('recipe.import-with-ai-image-provider-required') }}
          </v-alert>
        </template>

        <v-checkbox
          v-model="translateRecipe"
          color="primary"
          hide-details
          :label="$t('recipe.should-translate-description')"
          :disabled="state.loading"
        />
        <div class="d-flex align-center">
          <v-checkbox
            v-model="createNewOrganizers"
            color="primary"
            hide-details
            :label="$t('recipe.create-new-organizers')"
            :disabled="state.loading"
          />
          <v-tooltip location="bottom" max-width="300">
            <template #activator="{ props: tooltipProps }">
              <v-icon v-bind="tooltipProps" size="small" class="ms-2">
                {{ $globals.icons.help }}
              </v-icon>
            </template>
            <span>{{ $t('recipe.create-new-organizers-hint') }}</span>
          </v-tooltip>
        </div>
        <div class="d-flex align-center">
          <v-checkbox
            v-model="includeTranscription"
            color="primary"
            hide-details
            :label="$t('recipe.include-transcription')"
            :disabled="state.loading"
          />
          <v-tooltip location="bottom" max-width="300">
            <template #activator="{ props: tooltipProps }">
              <v-icon v-bind="tooltipProps" size="small" class="ms-2">
                {{ $globals.icons.help }}
              </v-icon>
            </template>
            <span>{{ $t('recipe.include-transcription-hint') }}</span>
          </v-tooltip>
        </div>
        <div class="d-flex align-center">
          <v-checkbox
            v-model="convertMeasurementSystem"
            color="primary"
            hide-details
            :label="$t('recipe.convert-measurement-system')"
            :disabled="state.loading"
          />
          <v-tooltip location="bottom" max-width="300">
            <template #activator="{ props: tooltipProps }">
              <v-icon v-bind="tooltipProps" size="small" class="ms-2">
                {{ $globals.icons.help }}
              </v-icon>
            </template>
            <span>{{ $t('recipe.convert-measurement-system-hint') }}</span>
          </v-tooltip>
        </div>
        <v-checkbox
          v-model="stayInEditMode"
          color="primary"
          hide-details
          :label="$t('recipe.stay-in-edit-mode')"
          :disabled="state.loading"
        />
        <v-checkbox
          v-model="parseRecipe"
          color="primary"
          hide-details
          :label="$t('recipe.parse-recipe-ingredients-after-import')"
          :disabled="state.loading"
        />
      </v-card-text>
      <v-card-actions v-if="aiEnabled" class="justify-center">
        <div style="width: 100%" class="text-center">
          <div style="width: 250px; margin: 0 auto">
            <BaseButton
              :disabled="!hasSource"
              rounded
              block
              type="submit"
              :loading="state.loading"
            />
          </div>
          <v-card-text class="py-2">
            <!-- render &nbsp; to maintain layout -->
            {{ createStatus }}&nbsp;
          </v-card-text>
        </div>
      </v-card-actions>

      <v-expand-transition>
        <v-alert
          v-if="state.error"
          color="error"
          class="mt-6 white--text"
        >
          <v-card-title class="ma-0 pa-0">
            <v-icon
              start
              color="white"
              size="x-large"
            >
              {{ $globals.icons.robot }}
            </v-icon>
            {{ $t("new-recipe.error-title") }}
          </v-card-title>
          <v-divider class="my-3 mx-2" />

          <div class="force-url-white">
            <p>{{ state.errorMessage || $t("recipe.import-with-ai-error-details") }}</p>
          </div>
        </v-alert>
      </v-expand-transition>
    </div>
  </v-form>
</template>

<script setup lang="ts">
import { useUserApi } from "~/composables/api";
import { useGroupSelf } from "~/composables/use-groups";
import { useTagStore } from "~/composables/store/use-tag-store";
import { useNewRecipeOptions } from "~/composables/use-new-recipe-options";
import { validators } from "~/composables/use-validators";
import type { VForm } from "~/types/auto-forms";

definePageMeta({
  key: route => route.path,
});

const state = reactive({
  error: false,
  errorMessage: "",
  loading: false,
  isEditJSON: false,
});

const i18n = useI18n();
const { $globals } = useNuxtApp();
const api = useUserApi();
const auth = useMealieAuth();
const route = useRoute();
const tags = useTagStore();
const { group } = useGroupSelf();

const groupSlug = computed(() => route.params.groupSlug as string || auth.user.value?.groupSlug || "");
const urlImporterTarget = computed(() => `/g/${groupSlug.value}/r/create/url`);
const htmlOrJsonImporterTarget = computed(() => `/g/${groupSlug.value}/r/create/html`);
const aiEnabled = computed(() => !!group.value?.aiProviderSettings?.aiEnabled);
const imagesEnabled = computed(() => !!group.value?.aiProviderSettings?.imageProviderEnabled);

type Source = "url" | "text" | "images" | "json";
const sources = ref<Source[]>(["url"]);
const has = (source: Source) => sources.value.includes(source);

const sourceOptions = computed(() => [
  { value: "url" as Source, icon: $globals.icons.link, label: i18n.t("recipe.import-source-link") },
  { value: "text" as Source, icon: $globals.icons.textBox, label: i18n.t("recipe.import-source-text") },
  { value: "images" as Source, icon: $globals.icons.fileImage, label: i18n.t("recipe.import-source-photos") },
  { value: "json" as Source, icon: $globals.icons.codeBraces, label: i18n.t("recipe.import-source-json") },
]);

function toggleSource(source: Source) {
  sources.value = has(source) ? sources.value.filter(item => item !== source) : [...sources.value, source];
}
const domUrlForm = ref<VForm | null>(null);
const recipeUrl = ref<string | null>(null);
const newRecipeData = ref<string | object | null>(null);
const uploadedImages = ref<(Blob | File)[]>([]);
const createStatus = ref<string | null>(null);

const {
  stayInEditMode,
  parseRecipe,
  translateRecipe,
  createNewOrganizers,
  includeTranscription,
  convertMeasurementSystem,
  navigateToRecipe,
} = useNewRecipeOptions({
  enableImportKeywords: false,
  enableImportCategories: false,
  enableTranslateRecipe: true,
  enableCreateNewOrganizers: true,
  enableIncludeTranscription: true,
  enableConvertMeasurementSystem: true,
});

const contentAsString = computed(() => {
  const data = newRecipeData.value;
  if (!data) {
    return null;
  }

  return typeof data === "string" ? data : JSON.stringify(data);
});

// every selected source is read together; hidden ones are not sent, whatever was typed in them
const activeUrl = computed(() => (has("url") ? recipeUrl.value : null));
const activeContent = computed(() => (has("text") || has("json") ? contentAsString.value : null));
const activeImages = computed(() => (has("images") ? uploadedImages.value : []));

const hasSource = computed(() => !!(activeUrl.value || activeContent.value || activeImages.value.length));

function handleIsEditJson() {
  if (state.isEditJSON) {
    if (newRecipeData.value) {
      try {
        newRecipeData.value = JSON.parse(newRecipeData.value as string);
      }
      catch {
        newRecipeData.value = { data: newRecipeData.value };
      }
    }
    else {
      newRecipeData.value = {};
    }
  }
  else if (newRecipeData.value && Object.keys(newRecipeData.value).length > 0) {
    newRecipeData.value = JSON.stringify(newRecipeData.value);
  }
  else {
    newRecipeData.value = null;
  }
}
handleIsEditJson();

// the JSON mode swaps the textarea for the code editor and carries the content across
watch(sources, (next, previous) => {
  // always keep one source, and let the text box and the JSON editor take turns (they share one value)
  if (!next.length) {
    sources.value = previous.length ? previous : ["url"];
    return;
  }
  if (next.includes("text") && next.includes("json")) {
    const added = next.find(source => !previous.includes(source));
    sources.value = next.filter(source => source !== (added === "json" ? "text" : "json"));
    return;
  }
  const wantsJson = next.includes("json");
  if (state.isEditJSON !== wantsJson) {
    state.isEditJSON = wantsJson;
    handleIsEditJson();
  }
});

async function createRecipe() {
  if (!hasSource.value) {
    return;
  }

  const isValid = await domUrlForm.value?.validate();
  if (!isValid?.valid) {
    return;
  }

  state.error = false;
  state.errorMessage = "";
  state.loading = true;

  const { data, error } = await api.recipes.createOneWithAI(
    {
      content: activeContent.value,
      url: activeUrl.value,
      images: activeImages.value,
      translateLanguage: translateRecipe.value ? i18n.locale.value : null,
      createNewOrganizers: createNewOrganizers.value,
      includeTranscription: includeTranscription.value,
      convertMeasurementSystem: convertMeasurementSystem.value,
    },
    (message: string) => createStatus.value = message,
  );

  createStatus.value = null;

  if (error || !data) {
    state.error = true;
    state.errorMessage = error?.message || "";
    state.loading = false;
    return;
  }

  if (createNewOrganizers.value) {
    tags.actions.refresh();
  }

  navigateToRecipe(data, groupSlug.value, `/g/${groupSlug.value}/r/create/ai`);
}
</script>

<style scoped>
.force-url-white a {
  color: white !important;
}
</style>
