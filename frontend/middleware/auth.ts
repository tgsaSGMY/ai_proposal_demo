// No-op passthrough — the demo has no authentication. Kept so existing
// `definePageMeta({ middleware: "auth" })` declarations still resolve.

export default defineNuxtRouteMiddleware(() => {
  return;
});
