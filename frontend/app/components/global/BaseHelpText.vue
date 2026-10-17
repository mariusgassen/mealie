<template>
  <div class="help-text">
    <button
      type="button"
      class="help-text__toggle text-primary"
      :aria-expanded="open"
      @click="open = !open"
    >
      <v-icon size="small">
        {{ $globals.icons.information }}
      </v-icon>
      {{ label || $t("general.more-info") }}
      <v-icon
        size="small"
        class="help-text__chevron"
        :class="{ 'help-text__chevron--open': open }"
      >
        {{ $globals.icons.chevronDown }}
      </v-icon>
    </button>
    <v-expand-transition>
      <div
        v-show="open"
        class="help-text__body text-medium-emphasis"
      >
        <slot />
      </div>
    </v-expand-transition>
  </div>
</template>

<script setup lang="ts">
/** Secondary explanation that stays out of the way until asked for. */
defineProps<{ label?: string }>();

const open = ref(false);
</script>

<style scoped>
.help-text__toggle {
  appearance: none;
  border: 0;
  background: none;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 0;
  font-size: 0.875rem;
  font-weight: 600;
}

.help-text__chevron {
  transition: transform 0.2s var(--mealie-ios-spring, ease);
}

.help-text__chevron--open {
  transform: rotate(180deg);
}

.help-text__body {
  padding-top: 4px;
  font-size: 0.875rem;
  line-height: 1.45;
}

.help-text__body :deep(p + p) {
  margin-top: 8px;
}
</style>
