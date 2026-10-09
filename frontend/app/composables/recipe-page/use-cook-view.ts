import { useLocalStorage } from "@vueuse/core";

export type CookView = "steps" | "all";

/** Which cooking-mode layout is shown: one step at a time, or the whole recipe scrolling. Remembered per device. */
export function useCookView() {
  return useLocalStorage<CookView>("mealie-cook-view", "steps");
}
