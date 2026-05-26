// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: "2025-07-15",
  devtools: { enabled: true },
  modules: ["@nuxtjs/tailwindcss", "@nuxt/icon", "nuxt-color-picker"],
  icon: {
    // Serve Nuxt icon endpoint outside /api to avoid proxying to backend
    localApiEndpoint: "/_nuxt_icon",
  },
  runtimeConfig: {
    public: {
      apiBaseUrl: process.env.NUXT_PUBLIC_API_BASE_URL || "",
      platformHomeUrl:
        process.env.NUXT_PUBLIC_PLATFORM_HOME_URL ||
        "https://portal.tgsaapp.com/",
      supabaseUrl: process.env.SUPABASE_URL || "",
      supabaseAnonKey: process.env.SUPABASE_ANON_KEY || "",
      demoGrantId: process.env.NUXT_PUBLIC_DEMO_GRANT_ID || "",
      demoTemplateId: process.env.NUXT_PUBLIC_DEMO_TEMPLATE_ID || "",
    },
  },
  routeRules: {
    "/projects/**": { ssr: false },
    "/": { ssr: false },
  },
});
