<template>
  <v-app-bar
    clipped-left
    density="compact"
    app
    color="primary"
    dark
    class="d-print-none ios-app-bar"
  >
    <slot />
    <v-btn
      icon
      color="white"
      @click="onLogoClick"
    >
      <v-icon size="40">
        {{ $globals.icons.primary }}
      </v-icon>
    </v-btn>

    <div
      btn
      class="pl-2"
    >
      <v-toolbar-title
        style="cursor: pointer"
        @click="$router.push(routerLink)"
      >
        <Transition
          name="ios-title"
          mode="out-in"
        >
          <span :key="collapsedTitle || 'app-name'">{{ collapsedTitle || "Mealie" }}</span>
        </Transition>
      </v-toolbar-title>
    </div>
    <RecipeDialogSearch ref="domSearchDialog" />

    <v-spacer />

    <slot name="actions" />

    <!-- Navigation Menu -->
    <template v-if="menu">
      <v-responsive
        v-if="!xs"
        max-width="250"
        @click="activateSearch"
      >
        <v-text-field
          readonly
          class="mt-1"
          rounded
          variant="solo-filled"
          density="compact"
          flat
          :prepend-inner-icon="$globals.icons.search"
          bg-color="primary-darken-1"
          :placeholder="$t('search.search-hint')"
        />
      </v-responsive>
      <v-btn
        v-else
        icon
        @click="activateSearch"
      >
        <v-icon> {{ $globals.icons.search }}</v-icon>
      </v-btn>
      <v-btn
        v-if="loggedIn"
        :variant="smAndUp ? 'text' : undefined"
        :icon="xs"
        @click="logout()"
      >
        <v-icon :start="smAndUp">
          {{ $globals.icons.logout }}
        </v-icon>
        {{ smAndUp ? $t("user.logout") : "" }}
      </v-btn>
      <v-btn
        v-else
        variant="text"
        nuxt
        to="/login"
      >
        <v-icon start>
          {{ $globals.icons.user }}
        </v-icon>
        {{ $t("user.login") }}
      </v-btn>
    </template>
  </v-app-bar>
</template>

<script setup lang="ts">
import { useLoggedInState } from "~/composables/use-logged-in-state";
import type RecipeDialogSearch from "~/components/Domain/Recipe/RecipeDialogSearch.vue";

const props = defineProps({
  menu: {
    type: Boolean,
    default: true,
  },
  // When true, tapping the logo below the md breakpoint toggles the sidebar instead of navigating home.
  logoTogglesSidebar: {
    type: Boolean,
    default: false,
  },
});
const auth = useMealieAuth();
const { loggedIn } = useLoggedInState();
const route = useRoute();
const groupSlug = computed(() => route.params.groupSlug as string || auth.user.value?.groupSlug || "");
const emit = defineEmits<{ (e: "toggle-sidebar"): void }>();
const { xs, smAndUp, mdAndUp } = useDisplay();
const collapsedTitle = useCollapsedTitle();

const routerLink = computed(() => groupSlug.value ? `/g/${groupSlug.value}` : "/");

function onLogoClick() {
  if (props.logoTogglesSidebar && !mdAndUp.value) {
    emit("toggle-sidebar");
  }
  else {
    navigateTo(routerLink.value);
  }
}
const domSearchDialog = ref<InstanceType<typeof RecipeDialogSearch> | null>(null);

function activateSearch() {
  domSearchDialog.value?.open();
}

function handleKeyEvent(e: KeyboardEvent) {
  const activeTag = document.activeElement?.tagName;
  if (e.key === "/" && activeTag !== "INPUT" && activeTag !== "TEXTAREA") {
    e.preventDefault();
    activateSearch();
  }
}

onMounted(() => {
  document.addEventListener("keydown", handleKeyEvent);
});

onBeforeUnmount(() => {
  document.removeEventListener("keydown", handleKeyEvent);
});

async function logout() {
  try {
    await auth.signOut("/login?direct=1");
  }
  catch (e) {
    console.error(e);
  }
}
</script>

<style scoped>
.v-toolbar {
  z-index: 2010 !important;
}

.ios-title-enter-active,
.ios-title-leave-active {
  transition:
    opacity 0.2s ease,
    transform 0.25s cubic-bezier(0.32, 0.72, 0, 1);
}

.ios-title-enter-from {
  opacity: 0;
  transform: translateY(8px);
}

.ios-title-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

.ios-app-bar {
  background-color: rgba(var(--v-theme-primary), 0.85) !important;
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
}
</style>
