<template>
  <div class="mt-4">
    <section
      class="d-flex flex-column"
      :class="$slots.header ? 'align-center' : 'align-start large-title'"
    >
      <slot name="header" />
      <h2
        ref="titleEl"
        class="text-h5"
      >
        <slot name="title">
          👋 Here's a Title
        </slot>
      </h2>

      <h3
        v-if="$slots.default"
        ref="subtitleEl"
        class="subtitle-1"
        :class="{ 'subtitle-1--clamped': !expanded }"
      >
        <slot />
      </h3>
      <button
        v-if="overflowing"
        type="button"
        class="subtitle-toggle text-primary"
        @click="expanded = !expanded"
      >
        {{ expanded ? $t("general.less") : $t("general.more") }}
      </button>
    </section>
    <section class="d-flex">
      <slot name="content" />
    </section>
    <v-divider
      v-if="divider"
      class="my-4"
    />
  </div>
</template>

<script setup lang="ts">
defineProps({
  divider: {
    type: Boolean,
    default: false,
  },
});

const titleEl = ref<HTMLElement | null>(null);
const subtitleEl = ref<HTMLElement | null>(null);
const expanded = ref(false);
const overflowing = ref(false);
const collapsedTitle = useCollapsedTitle();
let observer: IntersectionObserver | null = null;

// Once the heading scrolls up under the app bar, hand its text to the header (iOS large title -> inline title).
onMounted(() => {
  // long descriptions are cut to two lines; only offer "More" when something is actually hidden
  if (subtitleEl.value) {
    overflowing.value = subtitleEl.value.scrollHeight > subtitleEl.value.clientHeight + 1;
  }
  if (!titleEl.value || typeof IntersectionObserver === "undefined") {
    return;
  }
  observer = new IntersectionObserver(
    ([entry]) => {
      if (!entry) {
        return;
      }
      const scrolledAbove = !entry.isIntersecting && entry.boundingClientRect.top < 0;
      collapsedTitle.value = scrolledAbove ? (titleEl.value?.textContent?.trim() ?? "") : "";
    },
    { rootMargin: "-64px 0px 0px 0px" },
  );
  observer.observe(titleEl.value);
});

onBeforeUnmount(() => {
  observer?.disconnect();
  collapsedTitle.value = "";
});
</script>

<style scoped>
.large-title h2 {
  font-size: 2rem !important;
  line-height: 2.4rem;
  font-weight: 700;
  letter-spacing: -0.03em;
}

.subtitle-1 {
  font-size: 0.9375rem;
  font-weight: normal;
  color: var(--v-text-caption);
}

.subtitle-1--clamped {
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  overflow: hidden;
}

.subtitle-toggle {
  appearance: none;
  border: 0;
  background: none;
  cursor: pointer;
  align-self: flex-start;
  padding: 2px 0;
  font-size: 0.875rem;
  font-weight: 600;
}

/* header illustrations: a small accent, not a hero */
:deep(.v-img) {
  width: 56px !important;
  max-width: 56px !important;
  max-height: 56px !important;
  margin-bottom: 4px;
}
</style>
