<template>
  <v-toolbar
    class="fixed-bar mt-0"
    style="z-index: 2; position: sticky; background: transparent; box-shadow: none;"
    density="compact"
    elevation="0"
  >
    <v-spacer />
    <div class="custom-btn-group ma-1">
      <v-tooltip location="bottom" color="info">
        <template #activator="{ props: tooltipProps }">
          <v-btn
            icon
            variant="flat"
            rounded="circle"
            size="small"
            color="info"
            v-bind="tooltipProps"
            @click="$emit('random')"
          >
            <v-icon size="x-large">
              {{ $globals.icons.diceMultiple }}
            </v-icon>
          </v-btn>
        </template>
        <span>{{ $t("general.random") }}</span>
      </v-tooltip>
      <RecipeFavoriteBadge
        v-if="loggedIn"
        class="ml-1"
        color="info"
        button-style
        :recipe-id="recipe.id!"
        show-always
      />
      <RecipeTimelineBadge
        v-if="loggedIn"
        class="ml-1"
        color="info"
        button-style
        :slug="recipe.slug"
        :recipe-name="recipe.name!"
      />
      <div v-if="loggedIn">
        <v-tooltip v-if="canEdit" location="bottom" color="info">
          <template #activator="{ props: tooltipProps }">
            <v-btn
              icon
              variant="flat"
              rounded="circle"
              size="small"
              color="info"
              class="ml-1"
              v-bind="tooltipProps"
              @click="$emit('edit', true)"
            >
              <v-icon size="x-large">
                {{ $globals.icons.edit }}
              </v-icon>
            </v-btn>
          </template>
          <span>{{ $t("general.edit") }}</span>
        </v-tooltip>
      </div>

      <RecipeContextMenu
        show-print
        :menu-top="false"
        :name="recipe.name!"
        :slug="recipe.slug!"
        :menu-icon="$globals.icons.dotsVertical"
        fab
        color="info"
        :card-menu="false"
        :recipe="recipe"
        :recipe-id="recipe.id!"
        :recipe-scale="recipeScale"
        :use-items="{
          edit: false,
          download: loggedIn,
          duplicate: loggedIn,
          mealplanner: loggedIn,
          shoppingList: loggedIn,
          print: true,
          printPreferences: true,
          share: loggedIn,
          recipeActions: true,
          delete: loggedIn,
        }"
        class="ml-1"
        @print="$emit('print')"
      />
    </div>
  </v-toolbar>
</template>

<script setup lang="ts">
import RecipeContextMenu from "./RecipeContextMenu/RecipeContextMenu.vue";
import RecipeFavoriteBadge from "./RecipeFavoriteBadge.vue";
import RecipeTimelineBadge from "./RecipeTimelineBadge.vue";
import type { Recipe } from "~/lib/api/types/recipe";

interface Props {
  recipe: Recipe;
  slug: string;
  recipeScale?: number;
  name: string;
  loggedIn?: boolean;
  recipeId: string;
  canEdit?: boolean;
}
withDefaults(defineProps<Props>(), {
  recipeScale: 1,
  loggedIn: false,
  canEdit: false,
});

defineEmits(["print", "edit", "random"]);
</script>

<style scoped>
.custom-btn-group {
  flex: 0, 1, auto;
  display: inline-flex;
}

.gapped {
  gap: 0.25rem;
}

.vertical {
  flex-direction: column !important;
}

.sticky {
  margin-left: auto;
  position: fixed !important;
  margin-top: 4.25rem;
}

.fixed-bar {
  position: sticky;
  top: 4.5em;
  z-index: 2;
  background: transparent !important;
  box-shadow: none !important;
  min-height: 0 !important;
  height: 48px;
  padding: 0 8px;
}

.fixed-bar-mobile {
  top: 1.5em !important;
}
</style>
