<template>
  <div class="recipe-hero">
    <!-- Hero: image with the title laid over a scrim; plain title block when there is no image -->
    <div
      class="recipe-hero__media"
      :class="{ 'recipe-hero__media--plain': !recipe.image }"
    >
      <RecipePageInfoCardImage
        v-if="recipe.image"
        :recipe="recipe"
        :height="heroHeight"
        class="recipe-hero__image"
      />
      <div
        v-if="recipe.image"
        class="recipe-hero__scrim d-print-none"
      />
      <div class="recipe-hero__titles">
        <h1 class="recipe-hero__title">
          {{ recipe.name }}
        </h1>
        <RecipeRating
          :key="recipe.slug"
          :model-value="recipe.rating"
          :recipe-id="recipe.id"
          :slug="recipe.slug"
          class="recipe-hero__rating"
        />
      </div>
    </div>

    <div class="recipe-hero__body">
      <SafeMarkdown
        v-if="recipe.description"
        :source="recipe.description"
        class="recipe-hero__description"
      />

      <!-- Key facts as one inset card -->
      <v-card
        v-if="hasFacts"
        flat
        class="recipe-facts"
      >
        <div
          v-if="recipe.recipeYieldQuantity || recipe.recipeYield"
          class="recipe-facts__item"
        >
          <RecipeYield
            :yield-quantity="recipe.recipeYieldQuantity"
            :yield-text="recipe.recipeYield"
            :scale="recipeScale"
          />
        </div>
        <div
          v-if="hasTime"
          class="recipe-facts__item"
        >
          <RecipeTimeCard
            container-class="d-flex flex-wrap justify-center"
            :prep-time="recipe.prepTime"
            :total-time="recipe.totalTime"
            :perform-time="recipe.performTime"
            :prep-time-seconds="recipe.prepTimeSeconds"
            :total-time-seconds="recipe.totalTimeSeconds"
            :perform-time-seconds="recipe.performTimeSeconds"
          />
        </div>
        <div
          v-if="isOwnGroup"
          class="recipe-facts__item"
        >
          <RecipeLastMade :recipe="recipe" />
        </div>
      </v-card>

      <v-btn
        v-if="canCook"
        size="large"
        color="primary"
        class="recipe-hero__cook d-print-none"
        @click="toggleCookMode()"
      >
        <v-icon start>
          {{ $globals.icons.primary }}
        </v-icon>
        {{ $t("recipe.cook-mode") }}
      </v-btn>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useLoggedInState } from "~/composables/use-logged-in-state";
import RecipeRating from "~/components/Domain/Recipe/RecipeRating.vue";
import RecipeLastMade from "~/components/Domain/Recipe/RecipeLastMade.vue";
import RecipeTimeCard from "~/components/Domain/Recipe/RecipeTimeCard.vue";
import RecipeYield from "~/components/Domain/Recipe/RecipeYield.vue";
import RecipePageInfoCardImage from "~/components/Domain/Recipe/RecipePage/RecipePageParts/RecipePageInfoCardImage.vue";
import { usePageState } from "~/composables/recipe-page/shared-state";
import type { Recipe } from "~/lib/api/types/recipe";
import type { NoUndefinedField } from "~/lib/api/types/non-generated";

interface Props {
  recipe: NoUndefinedField<Recipe>;
  recipeScale?: number;
  // kept for API compatibility; the hero layout no longer depends on it
  landscape?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  recipeScale: 1,
  landscape: false,
});

const { isOwnGroup } = useLoggedInState();
const display = useDisplay();
const { isEditMode, toggleCookMode } = usePageState(props.recipe.slug);

const heroHeight = computed(() => (display.xs.value ? "280" : "400"));

const hasTime = computed(() => {
  const { prepTime, totalTime, performTime, prepTimeSeconds, totalTimeSeconds, performTimeSeconds } = props.recipe;
  return [prepTime, totalTime, performTime, prepTimeSeconds, totalTimeSeconds, performTimeSeconds].some(x => !!x);
});

const hasFacts = computed(() => {
  return !!(props.recipe.recipeYieldQuantity || props.recipe.recipeYield) || hasTime.value || isOwnGroup.value;
});

const canCook = computed(() => !isEditMode.value && (props.recipe.recipeInstructions?.length ?? 0) > 0);
</script>

<style scoped>
.recipe-hero__media {
  position: relative;
  overflow: hidden;
  background: rgb(var(--v-theme-surface-variant));
}

@media (min-width: 960px) {
  .recipe-hero__media {
    border-radius: 20px;
  }
}

.recipe-hero__media--plain {
  background: transparent;
  /* right padding keeps long titles clear of the floating action buttons */
  padding: 24px 104px 8px 16px;
}

.recipe-hero__scrim {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.72) 0%, rgba(0, 0, 0, 0.28) 45%, rgba(0, 0, 0, 0) 70%);
}

.recipe-hero__titles {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.recipe-hero__media:not(.recipe-hero__media--plain) .recipe-hero__titles {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  padding: 16px 20px 18px;
  color: #fff;
  pointer-events: none;
}

/* the rating stays tappable on top of the scrim, on a frosted pill so it reads on any photo */
.recipe-hero__media:not(.recipe-hero__media--plain) .recipe-hero__rating {
  pointer-events: auto;
  align-self: flex-start;
  padding: 0 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.22);
  backdrop-filter: blur(14px) saturate(160%);
  -webkit-backdrop-filter: blur(14px) saturate(160%);
}

.recipe-hero__media--plain .recipe-hero__rating {
  align-self: flex-start;
}

.recipe-hero__title {
  font-size: 1.9rem;
  line-height: 2.2rem;
  font-weight: 700;
  letter-spacing: -0.03em;
  text-wrap: balance;
  text-shadow: 0 1px 12px rgba(0, 0, 0, 0.25);
}

.recipe-hero__media--plain .recipe-hero__title {
  text-shadow: none;
}

@media (min-width: 960px) {
  .recipe-hero__title {
    font-size: 2.6rem;
    line-height: 3rem;
  }
}

.recipe-hero__body {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 16px 16px 0;
}

@media (min-width: 960px) {
  .recipe-hero__body {
    padding-inline: 4px;
  }
}

.recipe-hero__description {
  font-size: 1.05rem;
  line-height: 1.6;
  opacity: 0.85;
}

.recipe-facts {
  display: flex;
  flex-wrap: wrap;
  align-items: stretch;
  border-radius: 14px;
}

.recipe-facts__item {
  flex: 1 1 140px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 14px 12px;
}

/* hairline between facts, like grouped table rows */
.recipe-facts__item + .recipe-facts__item {
  border-inline-start: 0.5px solid var(--mealie-ios-separator);
}

@media (max-width: 599px) {
  .recipe-facts__item {
    flex-basis: 100%;
  }

  .recipe-facts__item + .recipe-facts__item {
    border-inline-start: 0;
    border-top: 0.5px solid var(--mealie-ios-separator);
  }
}

.recipe-hero__cook {
  font-weight: 600;
  border-radius: 14px;
  width: 100%;
}

@media (min-width: 600px) {
  .recipe-hero__cook {
    width: auto;
    min-width: 240px;
    align-self: flex-start;
  }
}
</style>
