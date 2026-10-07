/**
 * Tags <html> with the direction of the current navigation so the page-transition CSS
 * (assets/ios-transitions.css) can slide forward navigations in from the right and
 * back navigations in from the left, like a UINavigationController push/pop.
 *
 * vue-router stores the entry's index in history.state.position. During a back/forward
 * (popstate) navigation that state already points at the destination, while for a normal
 * push it still points at the current entry, so comparing it to the last settled position
 * tells the two apart.
 */
export default defineNuxtPlugin(() => {
  const router = useRouter();
  let lastPosition: number = history.state?.position ?? 0;

  router.beforeEach(() => {
    const position: number = history.state?.position ?? lastPosition;
    document.documentElement.dataset.navDirection = position < lastPosition ? "back" : "forward";
  });

  router.afterEach(() => {
    lastPosition = history.state?.position ?? lastPosition;
  });
});
