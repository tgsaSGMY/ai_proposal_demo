// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: "2025-07-15",
  devtools: { enabled: true },
  modules: ["@nuxtjs/tailwindcss", "@nuxt/icon"],
  runtimeConfig: {
    public: {
      apiBaseUrl:
        process.env.NUXT_PUBLIC_API_BASE_URL || "http://localhost:8000",
      supabaseUrl: process.env.SUPABASE_URL || "",
      supabaseAnonKey: process.env.SUPABASE_ANON_KEY || "",
    },
  },
  routeRules: {
    // 強制指令庫頁面只在瀏覽器端渲染 (SPA 模式)
    // 這樣伺服器就不會嘗試執行頁面邏輯，直接回傳空殼 HTML，避免 500 錯誤
    "/command-library": { ssr: false },
    "/plan-library": { ssr: false },
    "/": { ssr: false },
  },
});
