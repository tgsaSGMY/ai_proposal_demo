<template>
  <div class="flex min-h-screen bg-gray-100 font-sans">
    <!-- 側邊欄 -->
    <aside
      class="w-64 flex-shrink-0 bg-gray-800 text-white flex flex-col p-4 sticky top-0 h-screen overflow-y-auto"
    >
      <div class="text-center py-4 mb-6">
        <h2 class="text-xl font-semibold">AI 計畫書平台</h2>
        <span class="text-xs text-gray-400">v0.1</span>
      </div>

      <nav class="flex-grow">
        <ul>
          <li>
            <NuxtLink
              to="/"
              class="flex items-center gap-3 px-4 py-2.5 rounded-lg transition-colors duration-200 hover:bg-gray-700"
              active-class="bg-indigo-600 text-white"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                class="h-5 w-5"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  fill-rule="evenodd"
                  d="M11.3 1.046A1 1 0 0112 2v1.999l4.763 4.763a1 1 0 01-1.414 1.414l-4.763-4.763V14a1 1 0 11-2 0V5.414L3.65 10.177a1 1 0 01-1.414-1.414L6.999 4V2a1 1 0 011.046-1.046.998.998 0 011.208.044l.046.046zM10 16a1 1 0 100 2 1 1 0 000-2z"
                  clip-rule="evenodd"
                />
              </svg>
              <span>計畫書生成</span>
            </NuxtLink>
          </li>
          <li class="mt-2">
            <NuxtLink
              to="/_builder/model"
              class="flex items-center gap-3 px-4 py-2.5 rounded-lg transition-colors duration-200 hover:bg-gray-700"
              active-class="bg-indigo-600 text-white"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                class="h-5 w-5"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  d="M5 4a1 1 0 00-2 0v7.268a2 2 0 000 3.464V16a1 1 0 102 0v-1.268a2 2 0 000-3.464V4zM11 4a1 1 0 10-2 0v1.268a2 2 0 000 3.464V16a1 1 0 102 0V8.732a2 2 0 000-3.464V4zM16 3a1 1 0 011 1v7.268a2 2 0 010 3.464V16a1 1 0 11-2 0v-1.268a2 2 0 010-3.464V4a1 1 0 011-1z"
                />
              </svg>
              <span>模型配置</span>
            </NuxtLink>
          </li>
          <li class="mt-2">
            <NuxtLink
              to="/_builder/dataset"
              class="flex items-center gap-3 px-4 py-2.5 rounded-lg transition-colors duration-200 hover:bg-gray-700"
              active-class="bg-indigo-600 text-white"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                class="h-5 w-5"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  d="M5 3a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2V5a2 2 0 00-2-2H5zM5 11a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2v-2a2 2 0 00-2-2H5zM11 5a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V5zM11 13a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"
                />
              </svg>
              <span>資料集更新</span>
            </NuxtLink>
          </li>
          <li class="mt-2">
            <NuxtLink
              to="/_builder/management"
              class="flex items-center gap-3 px-4 py-2.5 rounded-lg transition-colors duration-200 hover:bg-gray-700"
              active-class="bg-indigo-600 text-white"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                class="h-5 w-5"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zM3 10a1 1 0 011-1h6a1 1 0 110 2H4a1 1 0 01-1-1zm0 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z"
                />
              </svg>
              <span>數據庫管理</span>
            </NuxtLink>
          </li>
        </ul>
      </nav>
    </aside>

    <!-- 主内容區 -->
    <main class="flex-1 overflow-y-auto h-screen">
      <slot />
    </main>
  </div>
</template>

<script setup></script>
