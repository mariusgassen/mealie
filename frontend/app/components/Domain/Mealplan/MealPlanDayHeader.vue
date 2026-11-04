<template>
  <v-card
    flat
    class="px-2"
    style="z-index: 2;"
    :color="endDate ? 'primary' : undefined"
    :variant="endDate ? 'tonal' : undefined"
  >
    <v-container class="px-0 d-flex align-center justify-space-between" height="48px">
      <p
        class="pl-2 text-subtitle-2 d-flex align-center ga-2"
        :class="isCurrent ? 'text-primary font-weight-bold' : 'font-weight-semibold'"
      >
        <span
          v-if="isCurrent && !endDate"
          class="plan-today-dot"
        />
        {{ $d(day, "short") }}<template v-if="endDate">
          - {{ $d(endDate, "short") }}
        </template>
      </p>
      <slot />
    </v-container>
  </v-card>
</template>

<script setup lang="ts">
import { endOfDay, isSameDay, isWithinInterval, startOfDay } from "date-fns";

interface Props {
  day: Date;
  /** Set for a week, whose meals aren't planned for a specific day */
  endDate?: Date | null;
};
const props = defineProps<Props>();

const isCurrent = computed(() => {
  const today = new Date();
  return props.endDate
    ? isWithinInterval(today, { start: startOfDay(props.day), end: endOfDay(props.endDate) })
    : isSameDay(props.day, today);
});
</script>

<style scoped>
.plan-today-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: rgb(var(--v-theme-primary));
}
</style>
