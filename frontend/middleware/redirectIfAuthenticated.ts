// No-op passthrough — login/signup pages don't exist in the demo.
// Kept so any leftover `middleware: "redirect-if-authenticated"`
// declarations resolve cleanly.

export default defineNuxtRouteMiddleware(() => {
  return;
});
