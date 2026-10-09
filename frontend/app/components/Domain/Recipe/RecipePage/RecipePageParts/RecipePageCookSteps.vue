<template>
  <div
    class="cook-steps d-print-none"
    role="dialog"
    :aria-label="recipe.name"
  >
    <!-- Top bar -->
    <header class="cook-steps__header">
      <v-btn
        icon
        variant="text"
        :aria-label="$t('general.close')"
        @click="$emit('close')"
      >
        <v-icon>{{ $globals.icons.close }}</v-icon>
      </v-btn>
      <div class="cook-steps__heading">
        <div class="cook-steps__recipe-name">
          {{ recipe.name }}
        </div>
        <div
          v-if="steps.length"
          class="cook-steps__progress-label"
        >
          {{ $t("recipe.cook-step-progress", { current: index + 1, total: steps.length }) }}
        </div>
      </div>
      <v-btn-toggle
        v-model="cookView"
        mandatory
        density="compact"
        class="cook-steps__view-toggle"
        :aria-label="$t('recipe.cook-mode')"
      >
        <v-btn value="steps" size="small">
          {{ $t("recipe.cook-view-steps") }}
        </v-btn>
        <v-btn value="all" size="small">
          {{ $t("recipe.cook-view-all") }}
        </v-btn>
      </v-btn-toggle>
    </header>

    <v-progress-linear
      :model-value="steps.length ? ((index + 1) / steps.length) * 100 : 0"
      height="4"
      color="primary"
      bg-color="transparent"
      class="cook-steps__bar"
    />

    <!-- Empty state -->
    <div
      v-if="!steps.length"
      class="cook-steps__empty"
    >
      <p class="text-h6">
        {{ $t("recipe.cook-no-steps") }}
      </p>
      <v-btn
        color="primary"
        @click="$emit('close')"
      >
        {{ $t("general.close") }}
      </v-btn>
    </div>

    <template v-else>
      <main
        class="cook-steps__main"
        @touchstart.passive="onTouchStart"
        @touchend.passive="onTouchEnd"
      >
        <!-- The step -->
        <section class="cook-steps__step">
          <Transition
            :name="direction === 'forward' ? 'cook-forward' : 'cook-back'"
            mode="out-in"
          >
            <div
              :key="index"
              class="cook-steps__step-inner"
            >
              <div
                v-if="sectionTitle"
                class="cook-steps__section"
              >
                {{ sectionTitle }}
              </div>
              <h2 class="cook-steps__title">
                <template v-if="step?.summary">
                  <SafeMarkdown :source="step.summary" />
                </template>
                <template v-else>
                  {{ $t("recipe.step-index", { step: index + 1 }) }}
                </template>
              </h2>
              <SafeMarkdown
                :source="step?.text ?? ''"
                class="cook-steps__text"
              />
            </div>
          </Transition>
        </section>

        <!-- Ingredients for this step: always on screen, at the scaled amount -->
        <aside
          class="cook-steps__ingredients"
          :aria-label="$t('recipe.cook-ingredients-for-step')"
        >
          <div class="cook-steps__ingredients-head">
            <h3 class="cook-steps__ingredients-title">
              {{ $t("recipe.cook-ingredients-for-step") }}
            </h3>
            <v-btn
              v-if="servingsLabel"
              variant="tonal"
              size="small"
              rounded
              @click="ingredientsSheet = true"
            >
              {{ $t("recipe.servings") }}: {{ servingsLabel }}
            </v-btn>
          </div>
          <ul
            v-if="stepIngredients.ingredients.length"
            class="cook-steps__ingredient-list"
          >
            <li
              v-for="(ingredient, i) in stepIngredients.ingredients"
              :key="ingredient.referenceId ?? i"
              class="cook-steps__ingredient"
            >
              <RecipeIngredientListItem
                :ingredient="ingredient"
                :scale="scale"
                show-substitutions
              />
            </li>
          </ul>
          <p
            v-else
            class="cook-steps__ingredients-empty"
          >
            {{ $t("recipe.cook-no-ingredients-for-step") }}
          </p>
          <p
            v-if="stepIngredients.source === 'matched'"
            class="cook-steps__ingredients-note"
          >
            <v-icon size="14" start>
              {{ $globals.icons.autoFix }}
            </v-icon>
            {{ $t("recipe.cook-ingredients-matched") }}
          </p>
        </aside>
      </main>

      <!-- Navigation -->
      <footer class="cook-steps__footer">
        <v-btn
          size="large"
          variant="tonal"
          :disabled="index === 0"
          :aria-label="$t('recipe.cook-previous-step')"
          @click="previous"
        >
          <v-icon>{{ $globals.icons.arrowLeftBold }}</v-icon>
        </v-btn>
        <v-btn
          size="large"
          variant="tonal"
          class="cook-steps__all-ingredients"
          :icon="xs"
          :aria-label="$t('recipe.cook-all-ingredients')"
          @click="ingredientsSheet = true"
        >
          <v-icon :start="!xs">
            {{ $globals.icons.formatListCheck }}
          </v-icon>
          <template v-if="!xs">
            {{ $t("recipe.cook-all-ingredients") }}
          </template>
        </v-btn>
        <v-btn
          size="large"
          color="primary"
          class="cook-steps__next"
          @click="next"
        >
          {{ isLast ? $t("general.done") : $t("recipe.nextStep") }}
        </v-btn>
      </footer>
    </template>

    <!-- Everything you need, with the usual check-off list -->
    <v-bottom-sheet
      v-model="ingredientsSheet"
      :z-index="2100"
      max-width="640"
    >
      <v-card class="cook-steps__sheet">
        <v-card-text class="cook-steps__sheet-body">
          <RecipePageScale
            v-model="scale"
            :recipe="recipe"
          />
          <RecipeIngredients
            :value="recipe.recipeIngredient"
            :scale="scale"
            :storage-key="ingredientStorageKey"
          />
          <WakelockSwitch />
        </v-card-text>
      </v-card>
    </v-bottom-sheet>
  </div>
</template>

<script setup lang="ts">
import { useEventListener, useSessionStorage } from "@vueuse/core";
import RecipeIngredientListItem from "~/components/Domain/Recipe/RecipeIngredientListItem.vue";
import RecipeIngredients from "~/components/Domain/Recipe/RecipeIngredients.vue";
import RecipePageScale from "~/components/Domain/Recipe/RecipePage/RecipePageParts/RecipePageScale.vue";
import { ingredientsForStep } from "~/composables/recipe-page/use-cook-step-ingredients";
import { useCookView } from "~/composables/recipe-page/use-cook-view";
import type { NoUndefinedField } from "~/lib/api/types/non-generated";
import type { Recipe } from "~/lib/api/types/recipe";

interface Props {
  recipe: NoUndefinedField<Recipe>;
  ingredientStorageKey?: string;
}
const props = withDefaults(defineProps<Props>(), {
  ingredientStorageKey: undefined,
});
const emit = defineEmits<{ (e: "close"): void }>();

const scale = defineModel<number>("scale", { default: 1 });
const { xs } = useDisplay();
const cookView = useCookView();

const steps = computed(() => props.recipe.recipeInstructions ?? []);

// Remember where you are if the page reloads mid-recipe
const storedIndex = useSessionStorage(`recipe-cook-step:${props.recipe.id || props.recipe.slug}`, 0);
const index = computed({
  get: () => Math.min(Math.max(storedIndex.value, 0), Math.max(steps.value.length - 1, 0)),
  set: (value: number) => {
    storedIndex.value = value;
  },
});

const step = computed(() => steps.value[index.value]);
const isLast = computed(() => index.value >= steps.value.length - 1);

// A step title starts a section, so the current section is the nearest title at or above this step
const sectionTitle = computed(() => {
  for (let i = index.value; i >= 0; i--) {
    const title = steps.value[i]?.title;
    if (title) {
      return title;
    }
  }
  return "";
});

// e.g. "4" or "2.5": servings at the current scale, shown so the amounts below can be trusted
const servingsLabel = computed(() => {
  const base = props.recipe.recipeServings || props.recipe.recipeYieldQuantity;
  if (!base) {
    return "";
  }
  return String(Math.round(base * scale.value * 100) / 100);
});

const stepIngredients = computed(() => ingredientsForStep(props.recipe.recipeIngredient ?? [], step.value));

const direction = ref<"forward" | "back">("forward");
const ingredientsSheet = ref(false);

function next() {
  if (isLast.value) {
    emit("close");
    return;
  }
  direction.value = "forward";
  index.value += 1;
}

function previous() {
  if (index.value === 0) {
    return;
  }
  direction.value = "back";
  index.value -= 1;
}

// Swipe left/right to move between steps (ignores mostly-vertical scrolls)
let touchStart: { x: number; y: number } | null = null;

function onTouchStart(event: TouchEvent) {
  const touch = event.changedTouches[0];
  touchStart = touch ? { x: touch.clientX, y: touch.clientY } : null;
}

function onTouchEnd(event: TouchEvent) {
  const touch = event.changedTouches[0];
  if (!touchStart || !touch) {
    return;
  }
  const dx = touch.clientX - touchStart.x;
  const dy = touch.clientY - touchStart.y;
  touchStart = null;

  if (Math.abs(dx) > 60 && Math.abs(dx) > Math.abs(dy) * 1.5) {
    if (dx < 0) {
      next();
    }
    else {
      previous();
    }
  }
}

useEventListener(window, "keydown", (event: KeyboardEvent) => {
  const tag = (event.target as HTMLElement | null)?.tagName;
  if (ingredientsSheet.value || tag === "INPUT" || tag === "TEXTAREA") {
    return;
  }
  if (event.key === "ArrowRight") {
    next();
  }
  else if (event.key === "ArrowLeft") {
    previous();
  }
  else if (event.key === "Escape") {
    emit("close");
  }
});
</script>

<style scoped>
.cook-steps {
  position: fixed;
  inset: 0;
  z-index: 2020;
  display: flex;
  flex-direction: column;
  background: rgb(var(--v-theme-background));
  padding: env(safe-area-inset-top) env(safe-area-inset-right) env(safe-area-inset-bottom) env(safe-area-inset-left);
}

.cook-steps__header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
}

.cook-steps__heading {
  flex: 1;
  min-width: 0;
}

.cook-steps__recipe-name {
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.cook-steps__progress-label {
  font-size: 0.8125rem;
  opacity: 0.65;
}

.cook-steps__bar {
  flex: 0 0 auto;
}

.cook-steps__main {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.cook-steps__step {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 20px 20px 12px;
}

.cook-steps__step-inner {
  max-width: 44rem;
  margin: 0 auto;
}

.cook-steps__section {
  font-size: 0.8125rem;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: rgb(var(--v-theme-primary));
  margin-bottom: 6px;
}

.cook-steps__title {
  font-size: 1.6rem;
  line-height: 1.25;
  font-weight: 700;
  letter-spacing: -0.02em;
  margin-bottom: 12px;
}

.cook-steps__text {
  font-size: 1.4rem;
  line-height: 1.65;
}

/* Ingredient panel: a raised card at the bottom on phones, a pinned column beside the step on wide screens */
.cook-steps__ingredients {
  flex: 0 1 auto;
  max-height: 55%;
  overflow-y: auto;
  margin: 0 12px 8px;
  padding: 12px 16px;
  border-radius: 16px;
  background: rgb(var(--v-theme-surface));
  border: 0.5px solid var(--mealie-ios-separator);
}

.cook-steps__ingredients-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 4px 12px;
}

.cook-steps__ingredients-title {
  font-size: 0.8125rem;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  opacity: 0.65;
}

.cook-steps__ingredient-list {
  list-style: none;
  padding: 0;
  margin: 4px 0 0;
}

.cook-steps__ingredient {
  padding: 6px 0;
  font-size: 1.15rem;
}

.cook-steps__ingredient + .cook-steps__ingredient {
  border-top: 0.5px solid var(--mealie-ios-separator);
}

.cook-steps__ingredient :deep(.ingredient-item) {
  font-size: 1.15rem;
}

.cook-steps__ingredients-empty,
.cook-steps__ingredients-note {
  margin: 8px 0 0;
  font-size: 0.9rem;
  opacity: 0.7;
}

.cook-steps__footer {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px 12px;
}

.cook-steps__all-ingredients {
  flex: 0 0 auto;
}

@media (min-width: 600px) {
  .cook-steps__all-ingredients {
    flex: 1;
    min-width: 0;
  }
}

.cook-steps__next {
  flex: 1;
  font-weight: 600;
}

@media (min-width: 600px) {
  .cook-steps__next {
    flex: 0 0 auto;
    min-width: 9rem;
  }
}

.cook-steps__empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
}

.cook-steps__sheet-body {
  max-height: 80dvh;
  overflow-y: auto;
}

@media (min-width: 960px) {
  .cook-steps__main {
    flex-direction: row;
    padding-bottom: 8px;
  }

  .cook-steps__step {
    flex: 1.5;
    padding: 32px 40px;
  }

  .cook-steps__text {
    font-size: 1.6rem;
  }

  .cook-steps__ingredients {
    flex: 1;
    max-height: none;
    max-width: 28rem;
    margin: 12px 12px 0 0;
  }

  .cook-steps__footer {
    max-width: 64rem;
    width: 100%;
    margin: 0 auto;
    padding-inline: 24px;
  }
}

/* step changes slide in the direction you are moving */
.cook-forward-enter-active,
.cook-forward-leave-active,
.cook-back-enter-active,
.cook-back-leave-active {
  transition:
    opacity 0.18s ease,
    transform 0.28s var(--mealie-ios-spring);
}

.cook-forward-enter-from,
.cook-back-leave-to {
  opacity: 0;
  transform: translateX(28px);
}

.cook-forward-leave-to,
.cook-back-enter-from {
  opacity: 0;
  transform: translateX(-28px);
}

@media (prefers-reduced-motion: reduce) {
  .cook-forward-enter-active,
  .cook-forward-leave-active,
  .cook-back-enter-active,
  .cook-back-leave-active {
    transition: none;
  }
}
</style>
