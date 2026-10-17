type RefreshHandler = () => Promise<unknown> | unknown;

// the handler of the page currently on screen; the layout-level indicator calls it when the user pulls down
const currentHandler = shallowRef<RefreshHandler | null>(null);

/** Lets a page opt in to pull-to-refresh: `usePullToRefresh(() => reload())` */
export function usePullToRefresh(handler: RefreshHandler) {
  onMounted(() => {
    currentHandler.value = handler;
  });

  onBeforeUnmount(() => {
    if (currentHandler.value === handler) {
      currentHandler.value = null;
    }
  });
}

export function usePullToRefreshHandler() {
  return currentHandler;
}
