/**
 * iOS-style large titles: BasePageTitle publishes its text here once it has
 * scrolled out of view, and AppHeader shows it in place of the app name.
 */
export function useCollapsedTitle() {
  return useState<string>("collapsed-page-title", () => "");
}
