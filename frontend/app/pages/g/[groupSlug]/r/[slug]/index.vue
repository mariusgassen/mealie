<template>
  <div>
    <RecipePage
      v-if="recipe"
      :key="recipe.slug"
      v-model="recipe"
    />
  </div>
</template>

<script setup lang="ts">
import { whenever } from "@vueuse/core";
import { useLoggedInState } from "~/composables/use-logged-in-state";
import { useAsyncKey } from "~/composables/use-utils";
import RecipePage from "~/components/Domain/Recipe/RecipePage/RecipePage.vue";
import { usePublicExploreApi } from "~/composables/api/api-client";
import { useRecipe } from "~/composables/recipes";
import type { Recipe } from "~/lib/api/types/recipe";

const auth = useMealieAuth();
const { isOwnGroup } = useLoggedInState();
const route = useRoute();
const title = ref(route.meta?.title as string || "");
useSeoMeta({ title });

const router = useRouter();

const recipe = ref<Recipe | null>(null);

async function loadRecipe(slug: string) {
  const { recipe: data, fetchRecipe } = useRecipe(slug, false);
  await fetchRecipe();
  recipe.value = data.value;
}

async function loadPublicRecipe(slug: string) {
  const groupSlug = computed(() => route.params.groupSlug as string || auth.user.value?.groupSlug || "");
  const api = usePublicExploreApi(groupSlug.value);
  const { data } = await useAsyncData(useAsyncKey(), async () => {
    const { data, error } = await api.explore.recipes.getOne(slug);
    if (error) {
      console.error("error loading recipe -> ", error);
      router.push({ path: `/g/${groupSlug.value}`, query: { redirect: route.fullPath } });
    }

    return data;
  });
  recipe.value = data.value;
}

// Navigating between two recipes (e.g. via the random recipe button) reuses this page
// instance, since the route only differs by the `slug` param, so loading must be re-run
// explicitly rather than relying on onMounted.
function loadCurrentRecipe() {
  const slug = route.params.slug as string;
  if (isOwnGroup.value) {
    loadRecipe(slug);
  }
  else {
    loadPublicRecipe(slug);
  }
}

onMounted(loadCurrentRecipe);
watch(() => route.params.slug, loadCurrentRecipe);

whenever(
  () => recipe.value,
  () => {
    if (recipe.value && recipe.value.name) {
      title.value = recipe.value.name;
    }
  },
);
</script>
