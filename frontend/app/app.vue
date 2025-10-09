<template>
  <div style="font-family: sans-serif; text-align: center; margin-top: 50px">
    <h1>Nuxt Frontend on Cloudflare Pages</h1>
    <h2>Connecting to FastAPI on Railway...</h2>

    <div
      style="
        margin-top: 30px;
        padding: 20px;
        border: 1px solid #ccc;
        border-radius: 8px;
        display: inline-block;
      "
    >
      <h3>API Call Status</h3>

      <!-- 正在加载时显示 -->
      <div v-if="pending">
        <p>⏳ Loading data from backend...</p>
      </div>

      <!-- 发生错误时显示 -->
      <div v-else-if="error" style="color: red">
        <p>❌ Error fetching data!</p>
        <pre
          style="
            text-align: left;
            background: #ffebeb;
            padding: 10px;
            border-radius: 4px;
          "
          >{{ error }}</pre
        >
      </div>

      <!-- 成功获取数据后显示 -->
      <div v-else-if="data" style="color: green">
        <p>✅ Successfully connected to the backend!</p>
        <div
          style="
            text-align: left;
            background: #e6ffed;
            padding: 15px;
            border-radius: 4px;
            margin-top: 10px;
          "
        >
          <p><strong>Message:</strong> {{ data.message }}</p>
          <p><strong>Timestamp (UTC):</strong> {{ data.timestamp }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<!-- app.vue -->
<script setup>
// 1. 获取在 nuxt.config.ts 和 Cloudflare 中配置的环境变量
const config = useRuntimeConfig();
const apiBaseUrl = config.public.apiBase; // 这就是 https://...up.railway.app

// 2. 使用 Nuxt 3 的 useFetch 来调用你的 FastAPI API
// 它会自动处理加载状态、错误和数据
const { data, pending, error } = useFetch("/api/greeting", {
  // baseURL 会自动加在 '/api/greeting' 前面
  baseURL: apiBaseUrl,

  // 'lazy: true' 意味着它不会阻塞页面导航，会在客户端获取数据
  lazy: true,

  // server: false 意味着这个请求只在客户端发起。
  // 对于测试 API 连通性，这样更直观。
  // 如果你想在服务器端渲染（SSR）时就获取数据，可以设为 true 或去掉这行。
  server: false,
});
</script>
