export default defineAppConfig({
  icon: {
    // Serve Nuxt icon assets via frontend (avoids /api proxy to backend)
    localApiEndpoint: "/_nuxt_icon",
  },
});
