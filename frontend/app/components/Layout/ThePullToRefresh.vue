<template>
  <div
    class="pull-indicator"
    :class="{ 'pull-indicator--settling': !pulling }"
    :style="{ transform: `translate(-50%, ${shift - 44}px)`, opacity }"
    aria-hidden="true"
  >
    <v-progress-circular
      :indeterminate="refreshing"
      :model-value="progress"
      :size="22"
      :width="3"
      color="primary"
    />
  </div>
</template>

<script setup lang="ts">
import { usePullToRefreshHandler } from "~/composables/use-pull-to-refresh";

/**
 * Pull-to-refresh for standalone/PWA use, where the browser's own gesture is not available. It only reacts to a
 * downward drag that starts at the very top of the page, and only when the page on screen registered a handler.
 */
const THRESHOLD = 64; // distance (after damping) that triggers a refresh
const MAX_PULL = 96;
const REFRESH_SHIFT = 52; // where the content rests while the refresh runs

const handler = usePullToRefreshHandler();

const pull = ref(0);
const pulling = ref(false);
const refreshing = ref(false);

let startX = 0;
let startY = 0;
let tracking = false;

const progress = computed(() => Math.min(pull.value / THRESHOLD, 1) * 100);
// how far the page content is pushed down to make room for the spinner, so it never covers anything
const shift = computed(() => (refreshing.value ? REFRESH_SHIFT : pull.value));
const opacity = computed(() => (refreshing.value ? 1 : Math.min(pull.value / THRESHOLD, 1)));

function overlayOpen() {
  return !!document.querySelector(".v-overlay--active");
}

function onTouchStart(event: TouchEvent) {
  const touch = event.touches[0];
  if (!touch || event.touches.length !== 1 || !handler.value || refreshing.value) {
    return;
  }

  tracking = window.scrollY <= 0 && !overlayOpen();
  startX = touch.clientX;
  startY = touch.clientY;
}

function onTouchMove(event: TouchEvent) {
  const touch = event.touches[0];
  if (!tracking || !touch) {
    return;
  }

  const dy = touch.clientY - startY;
  const dx = Math.abs(touch.clientX - startX);

  // upward, sideways or already scrolled: this is not a pull
  if (dy <= 0 || dx > dy || window.scrollY > 0) {
    reset();
    return;
  }

  pulling.value = true;
  pull.value = Math.min(dy * 0.5, MAX_PULL);
}

async function onTouchEnd() {
  if (!tracking) {
    return;
  }
  tracking = false;

  if (pull.value < THRESHOLD || !handler.value) {
    reset();
    return;
  }

  pulling.value = false;
  refreshing.value = true;
  try {
    await handler.value();
  }
  finally {
    refreshing.value = false;
    reset();
  }
}

function reset() {
  tracking = false;
  pulling.value = false;
  pull.value = 0;
}

watch([shift, pulling], ([value, isPulling]) => {
  const root = document.documentElement;
  root.style.setProperty("--ptr-shift", `${value}px`);
  root.classList.toggle("ptr-active", value > 0);
  root.classList.toggle("ptr-settling", !isPulling);
});

onMounted(() => {
  document.addEventListener("touchstart", onTouchStart, { passive: true });
  document.addEventListener("touchmove", onTouchMove, { passive: true });
  document.addEventListener("touchend", onTouchEnd, { passive: true });
  document.addEventListener("touchcancel", reset, { passive: true });
});

onBeforeUnmount(() => {
  document.documentElement.classList.remove("ptr-active", "ptr-settling");
  document.documentElement.style.removeProperty("--ptr-shift");
  document.removeEventListener("touchstart", onTouchStart);
  document.removeEventListener("touchmove", onTouchMove);
  document.removeEventListener("touchend", onTouchEnd);
  document.removeEventListener("touchcancel", reset);
});
</script>

<style scoped>
.pull-indicator {
  position: fixed;
  top: calc(var(--mealie-header-height, 48px) + env(safe-area-inset-top));
  left: 50%;
  z-index: 1999; /* below the app bar (2010), so the spinner slides out from underneath it */
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: rgb(var(--v-theme-surface));
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.18);
  pointer-events: none;
  opacity: 0;
}

.pull-indicator--settling {
  transition:
    transform 0.2s var(--mealie-ios-spring, ease),
    opacity 0.2s;
}
</style>

<style>
/* only transformed while a pull is active: a transform would otherwise trap position:fixed descendants */
.ptr-active .v-main {
  transform: translateY(var(--ptr-shift, 0px));
}

.ptr-active.ptr-settling .v-main {
  transition: transform 0.2s var(--mealie-ios-spring, ease);
}
</style>
