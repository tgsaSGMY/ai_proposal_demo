<template>
  <div class="min-h-screen bg-gray-50 font-sans flex flex-col md:flex-row">
    <header
      class="md:hidden bg-white text-gray-900 flex items-center justify-between px-4 py-3 border-b border-gray-200 sticky top-0 z-40"
    >
      <img src="/AI補助引擎_Logo_留邊.png" alt="AI 補助引擎" class="h-8 w-auto pointer-events-none select-none" />
      <button @click="showSidebar = !showSidebar" class="focus:outline-none">
        <svg
          v-if="!showSidebar"
          xmlns="http://www.w3.org/2000/svg"
          class="h-7 w-7"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M4 6h16M4 12h16M4 18h16"
          />
        </svg>
        <svg
          v-else
          xmlns="http://www.w3.org/2000/svg"
          class="h-7 w-7"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M6 18L18 6M6 6l12 12"
          />
        </svg>
      </button>
    </header>

    <aside
      :class="[
        showSidebar ? 'block' : 'hidden',
        'md:block',
        'w-full flex-shrink-0 bg-white border-r border-gray-100 shadow-sm transition-[width] duration-200',
        isSidebarCollapsed ? 'md:w-20' : 'md:w-72 lg:w-80',
        showSidebar
          ? 'fixed top-0 left-0 h-full z-50 overflow-y-auto md:static md:h-screen'
          : 'md:sticky md:top-0 md:h-screen md:overflow-y-auto md:z-30',
      ]"
      style="max-width: 100vw"
    >
      <div
        v-if="showSidebar"
        class="md:hidden sticky top-0 bg-white z-50 flex items-center justify-between px-4 py-3 border-b border-gray-200"
      >
        <img src="/AI補助引擎_Logo_留邊.png" alt="AI 補助引擎" class="h-8 w-auto pointer-events-none select-none" />
        <button @click="showSidebar = false" class="focus:outline-none">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="h-7 w-7"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      </div>

      <div
        class="flex h-full flex-col p-5"
        :class="isSidebarCollapsed ? 'md:p-3' : 'md:p-6'"
      >
        <!--
          側邊欄頂端：品牌 logo + 收合切換按鈕
          - 展開模式：logo 與切換按鈕並排（logo 左，按鈕右）
          - 收合模式：logo 置中，下方顯示切換按鈕（icon-only rail）
          切換按鈕僅在 md+ 顯示，移動端使用既有的 showSidebar 開關。
        -->
        <div
          class="flex items-center px-2"
          :class="isSidebarCollapsed ? 'md:flex-col md:gap-2 md:px-0' : 'gap-2 justify-between'"
        >
          <div
            class="flex flex-col min-w-0"
            :class="isSidebarCollapsed ? 'md:items-center md:w-full' : 'items-start'"
          >
            <img
              :src="
                isSidebarCollapsed
                  ? '/AI補助引擎.png'
                  : '/AI補助引擎_Logo_留邊.png'
              "
              alt="AI 補助引擎"
              class="pointer-events-none select-none max-w-full"
              :class="isSidebarCollapsed ? 'h-7 w-auto' : 'h-14 w-auto'"
            />
            <p
              v-if="isInternal && !isSidebarCollapsed"
              class="mt-2 text-[11px] uppercase tracking-wide text-gray-400"
            >
              内部人員版本
            </p>
          </div>

          <!-- 收合 / 展開切換按鈕（僅桌面端顯示） -->
          <button
            type="button"
            class="hidden md:inline-flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg border border-gray-100 bg-white text-gray-500 transition hover:border-rose-200 hover:bg-rose-50 hover:text-rose-500"
            :title="isSidebarCollapsed ? '展開側邊欄' : '收合側邊欄'"
            :aria-label="isSidebarCollapsed ? '展開側邊欄' : '收合側邊欄'"
            @click="toggleSidebarCollapsed"
          >
            <Icon
              :name="
                isSidebarCollapsed
                  ? 'tabler:layout-sidebar-left-expand'
                  : 'tabler:layout-sidebar-left-collapse'
              "
              class="h-4 w-4"
            />
          </button>
        </div>

        <nav class="mt-8 flex-1" aria-label="主選單">
          <template v-if="isAuthenticated">
            <div v-if="!isInternalView" class="space-y-3">
              <NuxtLink
                to="/"
                class="flex items-center rounded-2xl py-4 transition hover:-translate-y-0.5 hover:shadow-md"
                :class="[
                  isSidebarCollapsed
                    ? 'justify-center px-2'
                    : 'justify-between px-5',
                  route.path === '/'
                    ? 'border border-rose-500 bg-rose-500 text-white shadow-lg shadow-rose-200'
                    : 'border border-gray-100 bg-white text-gray-500 shadow-sm hover:border-rose-200 hover:bg-rose-50 hover:text-rose-600',
                ]"
                title="新計畫案啓動"
                @click="handleNavClick"
              >
                <div
                  class="flex items-center"
                  :class="isSidebarCollapsed ? '' : 'gap-3'"
                >
                  <span
                    class="flex h-10 w-10 items-center justify-center rounded-full border-2 border-rose-300 bg-white text-rose-500"
                  >
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke-width="2"
                      stroke="currentColor"
                      class="h-5 w-5"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        d="M12 6v12m6-6H6"
                      />
                    </svg>
                  </span>
                  <span
                    v-if="!isSidebarCollapsed"
                    class="text-base font-semibold"
                    >新計畫案啓動</span
                  >
                </div>
              </NuxtLink>

              <NuxtLink
                to="/plan-library"
                class="flex items-center rounded-2xl py-4 transition"
                :class="[
                  isSidebarCollapsed
                    ? 'justify-center px-2'
                    : 'justify-between px-5',
                  route.path.startsWith('/plan-library')
                    ? 'border border-rose-500 bg-rose-500 text-white shadow-lg shadow-rose-200'
                    : 'border border-gray-100 bg-white text-gray-500 shadow-sm hover:border-rose-200 hover:bg-rose-50 hover:text-rose-600',
                ]"
                title="我的計畫庫"
                @click.native="handleNavClick"
              >
                <div
                  class="flex items-center"
                  :class="isSidebarCollapsed ? '' : 'gap-3'"
                >
                  <span
                    class="flex h-10 w-10 items-center justify-center rounded-full bg-gray-50 text-gray-400"
                  >
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke-width="1.5"
                      stroke="currentColor"
                      class="h-6 w-6"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        d="M3 7h5l2 2h11v8a2 2 0 01-2 2H4a2 2 0 01-2-2V9a2 2 0 012-2z"
                      />
                    </svg>
                  </span>
                  <span
                    v-if="!isSidebarCollapsed"
                    class="text-base font-medium"
                    >我的計畫庫</span
                  >
                </div>
              </NuxtLink>

              <NuxtLink
                to="/command-library"
                class="flex items-center rounded-2xl py-4 transition"
                :class="[
                  isSidebarCollapsed
                    ? 'justify-center px-2'
                    : 'justify-between px-5',
                  route.path.startsWith('/command-library')
                    ? 'border border-rose-500 bg-rose-500 text-white shadow-lg shadow-rose-200'
                    : 'border border-gray-100 bg-white text-gray-500 shadow-sm hover:border-rose-200 hover:bg-rose-50 hover:text-rose-600',
                ]"
                title="我的背景資料"
                @click.native="handleNavClick"
              >
                <div
                  class="flex items-center"
                  :class="isSidebarCollapsed ? '' : 'gap-3'"
                >
                  <span
                    class="flex h-10 w-10 items-center justify-center rounded-full bg-gray-50 text-gray-400"
                  >
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke-width="1.5"
                      stroke="currentColor"
                      class="h-6 w-6"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        d="M7 5h10a2 2 0 012 2v12l-7-3-7 3V7a2 2 0 012-2z"
                      />
                    </svg>
                  </span>
                  <span
                    v-if="!isSidebarCollapsed"
                    class="text-base font-medium"
                    >我的背景資料</span
                  >
                </div>
              </NuxtLink>

              <!-- 説明中心按鈕：打開教學影片彈窗 -->
              <button
                class="flex w-full items-center rounded-2xl border border-gray-100 bg-white py-4 text-gray-500 shadow-sm transition hover:border-rose-200 hover:bg-rose-50 hover:text-rose-600"
                :class="
                  isSidebarCollapsed
                    ? 'justify-center px-2'
                    : 'justify-between px-5'
                "
                title="説明中心"
                @click="openHelpCenter"
              >
                <div
                  class="flex items-center"
                  :class="isSidebarCollapsed ? '' : 'gap-3'"
                >
                  <span
                    class="flex h-10 w-10 items-center justify-center rounded-full bg-gray-50 text-gray-400"
                  >
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke-width="1.5"
                      stroke="currentColor"
                      class="h-6 w-6"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                      />
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        d="M15.91 11.672a.375.375 0 010 .656l-5.603 3.113a.375.375 0 01-.557-.328V8.887c0-.286.307-.466.557-.327l5.603 3.112z"
                      />
                    </svg>
                  </span>
                  <span
                    v-if="!isSidebarCollapsed"
                    class="text-base font-medium"
                    >説明中心</span
                  >
                </div>
              </button>
            </div>

            <div v-else class="space-y-2">
              <p
                v-if="!isSidebarCollapsed"
                class="text-xs uppercase tracking-wide text-gray-400 px-1"
              >
                內部作業
              </p>
              <NuxtLink
                to="/_builder/template-manager"
                class="flex items-center rounded-xl py-3 text-gray-600 transition hover:bg-gray-900 hover:text-white"
                :class="
                  isSidebarCollapsed
                    ? 'justify-center px-2'
                    : 'gap-3 px-4'
                "
                active-class="bg-gray-900 text-white shadow-md"
                title="主題與模板管理"
                @click.native="handleNavClick"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  class="h-5 w-5 flex-shrink-0"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    d="M4 4a2 2 0 012-2h8a2 2 0 012 2v12a1 1 0 110 2h-3a1 1 0 01-1-1v-2a1 1 0 00-1-1H9a1 1 0 00-1 1v2a1 1 0 01-1 1H4a1 1 0 110-2V4z"
                  />
                </svg>
                <span v-if="!isSidebarCollapsed">主題與模板管理</span>
              </NuxtLink>
              <NuxtLink
                to="/_builder/model"
                class="flex items-center rounded-xl py-3 text-gray-600 transition hover:bg-gray-900 hover:text-white"
                :class="
                  isSidebarCollapsed
                    ? 'justify-center px-2'
                    : 'gap-3 px-4'
                "
                active-class="bg-gray-900 text-white shadow-md"
                title="模型配置"
                @click.native="handleNavClick"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  class="h-5 w-5 flex-shrink-0"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    d="M5 4a1 1 0 00-2 0v7.268a2 2 0 000 3.464V16a1 1 0 102 0v-1.268a2 2 0 000-3.464V4zM11 4a1 1 0 10-2 0v1.268a2 2 0 000 3.464V16a1 1 0 102 0V8.732a2 2 0 000-3.464V4zM16 3a1 1 0 011 1v7.268a2 2 0 010 3.464V16a1 1 0 11-2 0v-1.268a2 2 0 010-3.464V4a1 1 0 011-1z"
                  />
                </svg>
                <span v-if="!isSidebarCollapsed">模型配置</span>
              </NuxtLink>
              <NuxtLink
                to="/_builder/section"
                class="flex items-center rounded-xl py-3 text-gray-600 transition hover:bg-gray-900 hover:text-white"
                :class="
                  isSidebarCollapsed
                    ? 'justify-center px-2'
                    : 'gap-3 px-4'
                "
                active-class="bg-gray-900 text-white shadow-md"
                title="動態欄位配置"
                @click.native="handleNavClick"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  class="h-5 w-5 flex-shrink-0"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    d="M5.5 13a3.5 3.5 0 01-.369-6.98 4 4 0 117.753-1.3A4.5 4.5 0 1113.5 13H11V9.413l1.293 1.293a1 1 0 001.414-1.414l-3-3a1 1 0 00-1.414 0l-3 3a1 1 0 001.414 1.414L9 9.414V13H5.5z"
                  />
                </svg>
                <span v-if="!isSidebarCollapsed">動態欄位配置</span>
              </NuxtLink>

              <NuxtLink
                to="/_builder/dataset"
                class="flex items-center rounded-xl py-3 text-gray-600 transition hover:bg-gray-900 hover:text-white"
                :class="
                  isSidebarCollapsed
                    ? 'justify-center px-2'
                    : 'gap-3 px-4'
                "
                active-class="bg-gray-900 text-white shadow-md"
                title="模擬數據生成"
                @click.native="handleNavClick"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  class="h-5 w-5 flex-shrink-0"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    d="M5 3a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2V5a2 2 0 00-2-2H5zM5 11a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2v-2a2 2 0 00-2-2H5zM11 5a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V5zM11 13a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"
                  />
                </svg>
                <span v-if="!isSidebarCollapsed">模擬數據生成</span>
              </NuxtLink>

              <NuxtLink
                to="/_builder/management"
                class="flex items-center rounded-xl py-3 text-gray-600 transition hover:bg-gray-900 hover:text-white"
                :class="
                  isSidebarCollapsed
                    ? 'justify-center px-2'
                    : 'gap-3 px-4'
                "
                active-class="bg-gray-900 text-white shadow-md"
                title="數據庫更新"
                @click.native="handleNavClick"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  class="h-5 w-5 flex-shrink-0"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zM3 10a1 1 0 011-1h6a1 1 0 110 2H4a1 1 0 01-1-1zm0 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z"
                  />
                </svg>
                <span v-if="!isSidebarCollapsed">數據庫更新</span>
              </NuxtLink>

              <NuxtLink
                to="/_builder/usage-analytics"
                class="flex items-center rounded-xl py-3 text-gray-600 transition hover:bg-gray-900 hover:text-white"
                :class="
                  isSidebarCollapsed
                    ? 'justify-center px-2'
                    : 'gap-3 px-4'
                "
                active-class="bg-gray-900 text-white shadow-md"
                title="用量分析"
                @click.native="handleNavClick"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  class="h-5 w-5 flex-shrink-0"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z"
                  />
                </svg>

                <span v-if="!isSidebarCollapsed">用量分析</span>
              </NuxtLink>
            </div>
          </template>

          <div v-else class="space-y-3">
            <NuxtLink
              to="/login"
              class="flex items-center rounded-2xl py-3 transition border border-rose-200 bg-rose-50 text-rose-600 shadow-sm hover:border-rose-300 hover:bg-rose-100 hover:text-rose-700"
              :class="
                isSidebarCollapsed
                  ? 'justify-center px-2'
                  : 'gap-3 px-5'
              "
              active-class="border border-rose-300 bg-rose-100 text-rose-700 shadow-md"
              title="登入"
              @click.native="handleNavClick"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                class="h-5 w-5 flex-shrink-0"
                fill="none"
                viewBox="0 0 24 24"
                stroke-width="1.8"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  d="M15.75 9V5.25m0 0h-3.75m3.75 0L10.5 10.5M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <span v-if="!isSidebarCollapsed" class="font-medium">登入</span>
            </NuxtLink>
          </div>
        </nav>

        <div v-if="isAuthenticated" class="mt-6 space-y-3">
          <!-- 使用者帳號卡：收合模式下隱藏（icon-only rail 上沒有意義） -->
          <div
            v-if="userEmail && !isSidebarCollapsed"
            class="px-4 py-3 rounded-2xl bg-gray-100 border border-gray-200"
          >
            <p class="text-xs text-gray-500 uppercase tracking-wide">
              使用者帳號
            </p>
            <p class="text-sm font-semibold text-gray-900 mt-1 break-all">
              {{ userEmail }}
            </p>
          </div>

          <!-- 切換到內部管理視圖：收合時顯示為 icon-only 方塊按鈕 -->
          <button
            v-if="!isInternalView && isInternal"
            class="rounded-2xl bg-gray-900 text-sm font-semibold text-white shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
            :class="
              isSidebarCollapsed
                ? 'flex h-10 w-full items-center justify-center'
                : 'w-full px-4 py-3'
            "
            title="進入調整參數界面"
            @click="switchToInternalView"
          >
            <Icon
              v-if="isSidebarCollapsed"
              name="tabler:settings-cog"
              class="h-5 w-5"
            />
            <span v-else>進入調整參數界面</span>
          </button>
          <button
            v-else-if="isInternalView && isInternal"
            class="rounded-2xl border border-gray-200 text-sm font-semibold text-gray-700 transition hover:-translate-y-0.5 hover:border-gray-300"
            :class="
              isSidebarCollapsed
                ? 'flex h-10 w-full items-center justify-center'
                : 'w-full px-4 py-3'
            "
            title="返回計畫填寫界面"
            @click="switchToExternalView"
          >
            <Icon
              v-if="isSidebarCollapsed"
              name="tabler:arrow-left"
              class="h-5 w-5"
            />
            <span v-else>返回計畫填寫界面</span>
          </button>

          <!-- 登出：收合時顯示登出 icon -->
          <button
            class="rounded-2xl border border-rose-100 bg-white text-sm font-semibold text-rose-600 shadow-sm transition hover:bg-rose-50"
            :class="
              isSidebarCollapsed
                ? 'flex h-10 w-full items-center justify-center'
                : 'w-full px-4 py-3'
            "
            title="返回 TGSA 平台首頁"
            @click="handleLogout"
          >
            <Icon
              v-if="isSidebarCollapsed"
              name="tabler:logout"
              class="h-5 w-5"
            />
            <span v-else>返回 TGSA 平台首頁</span>
          </button>
        </div>
      </div>
    </aside>

    <main class="flex-1 overflow-y-auto min-h-screen">
      <slot />
    </main>

    <!-- 説明中心彈窗：背景模糊 + YouTube 教學影片 -->
    <Teleport to="body">
      <Transition
        enter-active-class="transition duration-200"
        enter-from-class="opacity-0"
        enter-to-class="opacity-100"
        leave-active-class="transition duration-150"
        leave-from-class="opacity-100"
        leave-to-class="opacity-0"
      >
        <div
          v-if="showHelpCenter"
          class="fixed inset-0 z-[100] flex items-center justify-center px-4 py-8"
        >
          <!-- 背景遮罩 -->
          <div
            class="absolute inset-0 bg-gray-900/50 backdrop-blur-sm"
            @click="showHelpCenter = false"
          ></div>
          <!-- 彈窗主體 -->
          <div
            class="relative w-full max-w-3xl rounded-3xl bg-white p-6 shadow-2xl"
          >
            <!-- 標題列 -->
            <div class="flex items-center justify-between mb-4">
              <div>
                <p
                  class="text-xs font-semibold uppercase tracking-wide text-rose-400"
                >
                  教學指南
                </p>
                <h3 class="text-xl font-semibold text-gray-900">説明中心</h3>
              </div>
              <button
                class="rounded-full p-2 text-gray-400 transition hover:bg-gray-100 hover:text-gray-700"
                @click="showHelpCenter = false"
                aria-label="關閉説明中心"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke-width="1.5"
                  stroke="currentColor"
                  class="h-5 w-5"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </div>
            <!-- 影片播放器 -->
            <div class="aspect-video w-full overflow-hidden rounded-2xl bg-gray-100">
              <iframe
                v-if="showHelpCenter"
                :src="helpCenterVideos[0].embedUrl"
                class="h-full w-full"
                frameborder="0"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowfullscreen
              ></iframe>
            </div>
            <p class="mt-3 text-sm text-gray-500">
              {{ helpCenterVideos[0].title }}
            </p>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>
<script setup>
// ===== 导入依赖库 =====
// 导入 Vue 核心库和相关函数
import { ref, onMounted, onBeforeUnmount, watch } from "vue";
import {
  appLogout,
  authenticatedFetch,
  getAppSession,
} from "~/composables/useAppAuth";
import { supabase } from "~/utils/supabaseClient";
// 导入自定义组合式函数
import { useCurrentUser } from "~/composables/useCurrentUser";

// ===== 路由和初始化 =====
// 获取 Vue Router 实例
const router = useRouter();
const route = useRoute();

// ===== UI 状态管理 =====
// 移动设备上侧边栏的显示/隐藏状态
const showSidebar = ref(false);
// 桌面端：侧边栏是否处于收合（icon-only）状态。仅在 md+ 生效，移动端无影响。
// 状态会持久化到 localStorage（key: tgsa.sidebarCollapsed），重新整理後仍保留。
const isSidebarCollapsed = ref(false);
const SIDEBAR_COLLAPSED_KEY = "tgsa.sidebarCollapsed";

function toggleSidebarCollapsed() {
  isSidebarCollapsed.value = !isSidebarCollapsed.value;
}

// 用户是否已认证
const isAuthenticated = ref(false);
// 权限：是否为内部人员
const isInternal = ref(false);
// 用户的总消费成本
const userTotalCost = ref(0);

// ===== 説明中心 =====
// 説明中心彈窗顯示狀態
const showHelpCenter = ref(false);
// 教學影片清單（未來可擴充多部影片）
const helpCenterVideos = ref([
  {
    title: "系統操作教學影片",
    embedUrl: "https://www.youtube.com/embed/489R0hTWn3Q",
  },
]);

function openHelpCenter() {
  showHelpCenter.value = true;
  // 移動端上點擊後自動關閉側邊欄
  handleNavClick();
}

// ===== 视图切换状态 =====
// 计算属性或 Watcher 来决定显示哪种侧边栏
// 这样可以确保"侧边栏"永远跟"当前网址"是对应的
const isInternalView = ref(false);

// ===== 侦听器：路由变化 =====
// 监听路由变化，自动切换侧边栏状态
watch(
  () => route.path,
  (newPath) => {
    // 如果路径以 /_builder 开头，且用户有权限，则显示内部视图
    if (newPath.startsWith("/_builder") && isInternal.value) {
      isInternalView.value = true;
    } else {
      isInternalView.value = false;
    }
  },
  { immediate: true },
);

// ===== 侧边栏收合状态持久化 =====
// 任何收合/展开操作都会同步写入 localStorage，使下次进入时保持上次的偏好。
watch(isSidebarCollapsed, (collapsed) => {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(SIDEBAR_COLLAPSED_KEY, collapsed ? "1" : "0");
  } catch (err) {
    console.warn("Failed to persist sidebar collapse state", err);
  }
});

// ===== 用户信息管理 =====
// 获取当前用户 ID 和刷新函数
const { userId: currentUserId, refreshUser } = useCurrentUser();
// 当前用户的电子邮件地址
const userEmail = ref("");
// 认证变化的订阅对象
let authSubscription = null;

// ===== API 配置 =====
// 获取运行时配置
const config = useRuntimeConfig();
// API 基础 URL
const API_BASE_URL = `${config.public.apiBaseUrl}/api`;
const TGSA_PLATFORM_HOME_URL =
  config.public.platformHomeUrl || "https://portal.tgsaapp.com/";

// ===== 事件处理函数 =====
// 处理侧边栏点击 (移动端关闭菜单)
function handleNavClick() {
  // 在移动设备上，点击菜单项后自动关闭侧边栏
  if (typeof window !== "undefined" && window.innerWidth < 768) {
    showSidebar.value = false;
  }
}

// ===== 视图切换功能 =====
// 切换到内部视图：跳转到内部管理员界面
// 管理员可以编辑方案模板、部分配置等
async function switchToInternalView() {
  // 跳转到内部管理员的模型编辑页面
  await router.push("/_builder/template-manager");
  // 移动端上自动关闭侧边栏
  handleNavClick();
}

// 切换回外部视图：跳转到普通用户的首页
async function switchToExternalView() {
  // 跳转到外部用户的首页
  await router.push("/");
  // 移动端上自动关闭侧边栏
  handleNavClick();
}

// ===== 用户成本/使用量管理 =====
// 获取指定用户的成本和使用量信息
// 参数: targetUserId - 要查询的用户 ID
async function fetchUserUsage(targetUserId) {
  // 如果没有提供用户 ID，则将使用量设为 null
  if (!targetUserId) {
    userTotalCost.value = null;
    return;
  }

  try {
    // 调用 API 获取用户成本信息
    const response = await authenticatedFetch(
      `${API_BASE_URL}/user-usage?user_id=${targetUserId}`,
    );
    // 如果响应失败，抛出错误
    if (!response.ok) throw new Error("Failed to fetch usage");
    const data = await response.json();
    // 将成本保存到状态，格式化为 2 位小数
    userTotalCost.value = Number(data.usage).toFixed(2);
  } catch (e) {
    // 如果出错，将使用量设为 null
    userTotalCost.value = null;
  }
}

// ===== 用户登出功能 =====
// 处理用户登出：清除认证状态，清理本地存储，重定向到登录页面
async function handleLogout() {
  try {
    await appLogout({ redirectTo: TGSA_PLATFORM_HOME_URL });
  } catch (error) {
    // 登出失败时打印错误信息
    console.error("Logout error:", error);
  }
}

// ===== 组件生命周期和初始化 =====
// 组件挂载时的初始化逻辑
// 在这里获取用户会话、检查权限、设置认证监听器
onMounted(async () => {
  // 从 localStorage 读取 sidebar 收合状态（仅在 client 端执行，避免 SSR 不一致）
  if (typeof window !== "undefined") {
    try {
      const stored = window.localStorage.getItem(SIDEBAR_COLLAPSED_KEY);
      if (stored === "1") {
        isSidebarCollapsed.value = true;
      }
    } catch (err) {
      // localStorage 在隐私模式下可能抛错，忽略即可
      console.warn("Failed to read sidebar collapse state", err);
    }
  }

  // 刷新用户信息缓存
  refreshUser();

  // 第 1 步：获取初始的认证会话
  const appSession = await getAppSession();
  // 使用会话信息更新本地状态
  await handleSessionUpdate(appSession);

  // 第 2 步：监听认证状态变化（包括用户切换标签页时的会话刷新）
  const {
    data: { subscription },
  } = supabase.auth.onAuthStateChange(() => {
    void (async () => {
      const latest = await getAppSession();
      await handleSessionUpdate(latest);
    })();
  });
  // 保存订阅对象以便在组件卸载时取消订阅
  authSubscription = subscription;
});

// ===== 处理会话状态更新 =====
// 统一处理所有与 Supabase 会话相关的状态逻辑
// 参数: session - Supabase 会话对象（可能为 null）
async function handleSessionUpdate(appSession) {
  // 和 middleware 保持一致：有 session 且有 user 才算已登入。
  isAuthenticated.value = appSession?.isAuthenticated === true;
  // 先放入 session email；稍後會用 /auth/me（users table）覆寫成 canonical email。
  userEmail.value = "";

  // 如果用户未认证，清除所有相关权限和数据
  if (!isAuthenticated.value) {
    isInternal.value = false;
    userTotalCost.value = null;
    userEmail.value = "";
    return;
  }

  let canonicalUserId = null;
  try {
    // 统一从后端 /auth/me 获取 canonical user（来源为 users table）。
    const meResponse = await authenticatedFetch(`${API_BASE_URL}/auth/me`);

    if (meResponse.ok) {
      const me = await meResponse.json();
      canonicalUserId = me?.id ?? null;
      currentUserId.value = canonicalUserId;
      userEmail.value = me?.email ?? userEmail.value;
      isInternal.value = me?.role === "internal";
    } else {
      // /auth/me 暫時失敗時，回退到既有流程。
      canonicalUserId = await refreshUser();
      currentUserId.value = canonicalUserId;
      const { checkIsInternal } = useInternalCheck();
      isInternal.value = await checkIsInternal();
    }
  } catch (error) {
    console.error("Failed to load canonical user profile", error);
    canonicalUserId = await refreshUser();
    currentUserId.value = canonicalUserId;
    const { checkIsInternal } = useInternalCheck();
    isInternal.value = await checkIsInternal();
  }

  // 对于已认证的用户：获取成本/使用量信息
  if (canonicalUserId) {
    fetchUserUsage(canonicalUserId);
  }

  // 强制检查一次路由状态，确保 isInternalView 标志准确
  // 如果路由是 /_builder 开头且用户有权限，则显示内部视图
  // 否则显示外部用户视图
  if (route.path.startsWith("/_builder") && isInternal.value) {
    isInternalView.value = true;
  } else {
    isInternalView.value = false;
  }
}

// ===== 组件卸载清理 =====
// 组件卸载前执行清理操作，防止内存泄漏
onBeforeUnmount(() => {
  // 取消 Supabase 认证状态变化的监听器订阅
  authSubscription?.unsubscribe();
});
</script>
