<template>
  <div class="recipe-header">
    <RecipePageInfoCard
      :recipe="recipe"
      :recipe-scale="recipeScale"
      :landscape="landscape"
    />
    <div :class="isEditMode ? 'd-flex justify-end px-4 py-3' : 'recipe-header__actions'">
      <RecipeActionMenu
        :recipe="recipe"
        :slug="recipe.slug"
        :recipe-scale="recipeScale"
        :can-edit="canEditRecipe"
        :name="recipe.name"
        :logged-in="isOwnGroup"
        :open="isEditMode"
        :recipe-id="recipe.id"
        @close="$emit('close')"
        @json="toggleEditMode()"
        @edit="setMode(PageMode.EDIT)"
        @save="$emit('save')"
        @delete="$emit('delete')"
        @print="printRecipe"
        @random="navigateRandom"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { useLoggedInState } from "~/composables/use-logged-in-state";
import { useRecipePermissions, useLazyRecipes } from "~/composables/recipes";
import RecipePageInfoCard from "~/components/Domain/Recipe/RecipePage/RecipePageParts/RecipePageInfoCard.vue";
import RecipeActionMenu from "~/components/Domain/Recipe/RecipeActionMenu.vue";
import { useStaticRoutes, useUserApi } from "~/composables/api";
import type { HouseholdSummary } from "~/lib/api/types/household";
import type { Recipe } from "~/lib/api/types/recipe";
import type { NoUndefinedField } from "~/lib/api/types/non-generated";
import { usePageState, usePageUser, PageMode } from "~/composables/recipe-page/shared-state";

interface Props {
  recipe: NoUndefinedField<Recipe>;
  recipeScale?: number;
  landscape?: boolean;
}
const props = withDefaults(defineProps<Props>(), {
  recipeScale: 1,
  landscape: false,
});

defineEmits(["save", "delete", "print", "close"]);

const { recipeImage } = useStaticRoutes();
const { imageKey, setMode, toggleEditMode, isEditMode } = usePageState(props.recipe.slug);
const { user } = usePageUser();
const { isOwnGroup } = useLoggedInState();

const route = useRoute();
const router = useRouter();
const auth = useMealieAuth();
const groupSlug = computed(() => (route.params.groupSlug as string) || auth.user.value?.groupSlug || "");

async function navigateRandom() {
  const { getRandom } = useLazyRecipes(isOwnGroup.value ? null : groupSlug.value);
  const recipe = await getRandom();
  if (!recipe?.slug) {
    return;
  }
  router.push(`/g/${groupSlug.value}/r/${recipe.slug}`);
}

const recipeHousehold = ref<HouseholdSummary>();
if (user) {
  const userApi = useUserApi();
  userApi.households.getOne(props.recipe.householdId).then(({ data }) => {
    recipeHousehold.value = data || undefined;
  });
}
const { canEditRecipe } = useRecipePermissions(props.recipe, recipeHousehold, user);

function printRecipe() {
  window.print();
}

const hideImage = ref(false);

const recipeImageUrl = computed(() => {
  return recipeImage(props.recipe.id, props.recipe.image, imageKey.value);
});

watch(
  () => recipeImageUrl.value,
  () => {
    hideImage.value = false;
  },
);
</script>

<style scoped>
.recipe-header {
  position: relative;
}

/* in view mode the actions float over the hero's top-right corner */
.recipe-header__actions {
  position: absolute;
  top: 12px;
  right: 12px;
  z-index: 2;
}
</style>
