<template>
  <v-card flat class="px-2" style="z-index: 2;">
    <v-container class="px-0 d-flex align-center justify-space-between" height="48px">
      <p
        class="pl-2 text-subtitle-2 d-flex align-center ga-2"
        :class="isToday(day) ? 'text-primary font-weight-bold' : 'font-weight-semibold'"
      >
        <span
          v-if="isToday(day)"
          class="plan-today-dot"
        />
        {{ $d(day, "short") }}
      </p>
      <slot />
    </v-container>
  </v-card>
</template>

<script setup lang="ts">
import { isSameDay } from "date-fns";

interface Props {
  day: Date;
};
defineProps<Props>();

const isToday = (date: Date) => {
  return isSameDay(date, new Date());
};
</script>

<style scoped>
.plan-today-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: rgb(var(--v-theme-primary));
}
</style>
