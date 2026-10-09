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

      <h3 class="subtitle-1">
        <slot />
      </h3>
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
const collapsedTitle = useCollapsedTitle();
let observer: IntersectionObserver | null = null;

// Once the heading scrolls up under the app bar, hand its text to the header (iOS large title -> inline title).
onMounted(() => {
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
  font-size: 1rem;
  font-weight: normal;
  color: var(--v-text-caption);
}
</style>
