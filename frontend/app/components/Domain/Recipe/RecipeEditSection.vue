<template>
  <section class="edit-section">
    <h3
      v-if="title"
      class="edit-section__title"
    >
      {{ title }}
    </h3>
    <v-card
      flat
      class="edit-section__card"
      :class="{ 'edit-section__card--flush': flush }"
    >
      <slot />
    </v-card>
    <p
      v-if="hint"
      class="edit-section__hint"
    >
      {{ hint }}
    </p>
  </section>
</template>

<script setup lang="ts">
/**
 * One group of fields in the recipe editor: a small caps heading above a rounded card, like an
 * inset grouped list in iOS Settings.
 */
defineProps<{
  title?: string;
  hint?: string;
  // no inner padding, for content that brings its own (lists, cards)
  flush?: boolean;
}>();
</script>

<style>
/* global on purpose: other editor components reuse the heading class so every section matches */
.edit-section {
  margin-bottom: 24px;
}

.edit-section__title {
  margin: 0 16px 8px;
  font-size: 0.8125rem;
  font-weight: 600;
  letter-spacing: 0.06em;
  line-height: 1.2;
  text-transform: uppercase;
  opacity: 0.6;
}

.edit-section__card {
  border-radius: 14px;
  padding: 16px;
}

.edit-section__card--flush {
  padding: 0;
}

.edit-section__hint {
  margin: 8px 16px 0;
  font-size: 0.8125rem;
  opacity: 0.6;
}
</style>
