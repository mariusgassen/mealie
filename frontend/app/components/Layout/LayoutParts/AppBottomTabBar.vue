<template>
  <nav class="ios-bottom-nav d-print-none">
    <v-btn
      v-for="tab in tabs"
      :key="tab.key"
      :to="tab.to"
      variant="text"
      class="ios-bottom-nav__tab"
      :class="{ 'ios-bottom-nav__tab--active': tab.to === route.path }"
    >
      <v-icon size="24">
        {{ tab.icon }}
      </v-icon>
      <span class="ios-bottom-nav__label">{{ tab.title }}</span>
    </v-btn>
    <v-btn
      variant="text"
      class="ios-bottom-nav__tab"
      :class="{ 'ios-bottom-nav__tab--active': sidebarOpen }"
      @click="sidebarOpen = !sidebarOpen"
    >
      <v-icon size="24">
        {{ $globals.icons.dotsHorizontal }}
      </v-icon>
      <span class="ios-bottom-nav__label">{{ $t('general.more') }}</span>
    </v-btn>
  </nav>
</template>

<script setup lang="ts">
import { useLoggedInState } from "~/composables/use-logged-in-state";

const i18n = useI18n();
const { $globals } = useNuxtApp();
const route = useRoute();
const auth = useMealieAuth();
const { isOwnGroup } = useLoggedInState();

const sidebarOpen = defineModel<boolean>("sidebarOpen", { default: false });

const groupSlug = computed(() => route.params.groupSlug as string || auth.user.value?.groupSlug || "");

const tabs = computed(() => {
  const allTabs = [
    {
      key: "recipes",
      icon: $globals.icons.silverwareForkKnife,
      title: i18n.t("general.recipes"),
      to: `/g/${groupSlug.value}`,
      restricted: false,
    },
    {
      key: "search",
      icon: $globals.icons.search,
      title: i18n.t("recipe-finder.recipe-finder"),
      to: `/g/${groupSlug.value}/recipes/finder`,
      restricted: false,
    },
    {
      key: "mealplan",
      icon: $globals.icons.calendarMultiselect,
      title: i18n.t("meal-plan.meal-planner"),
      to: "/household/mealplan/planner/view",
      restricted: true,
    },
    {
      key: "shopping-lists",
      icon: $globals.icons.formatListCheck,
      title: i18n.t("shopping-list.shopping-lists"),
      to: "/shopping-lists",
      restricted: true,
    },
  ];

  return allTabs.filter(tab => !tab.restricted || isOwnGroup.value);
});
</script>

<style scoped>
.ios-bottom-nav {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 2005;
  display: flex;
  align-items: stretch;
  height: calc(var(--mealie-bottom-nav-height) + env(safe-area-inset-bottom));
  padding-bottom: env(safe-area-inset-bottom);
  padding-left: env(safe-area-inset-left);
  padding-right: env(safe-area-inset-right);
  background-color: rgba(var(--v-theme-surface), 0.85);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.ios-bottom-nav__tab {
  flex: 1 1 0;
  height: 100%;
  min-width: 0;
  border-radius: 0;
  color: rgba(var(--v-theme-on-surface), 0.6);
  font-size: 10px;
}

.ios-bottom-nav__tab :deep(.v-btn__content) {
  flex-direction: column;
  gap: 2px;
}

.ios-bottom-nav__tab--active {
  color: rgb(var(--v-theme-primary));
}

.ios-bottom-nav__label {
  line-height: 1;
  font-size: 10px;
  text-transform: none;
}
</style>
