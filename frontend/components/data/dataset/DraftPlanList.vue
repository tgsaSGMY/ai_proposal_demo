<!-- 方案草稿列表组件：显示正在编辑的方案草稿 -->
<template>
  <div>
    <!-- Filter Controls -->
    <div
      class="mb-4 sm:mb-6 flex flex-col sm:flex-row items-center gap-2 sm:gap-4"
    >
      <input
        type="text"
        v-model="searchTerm"
        placeholder="搜索計畫名稱..."
        class="w-full max-w-full sm:max-w-xs px-3 sm:px-4 py-2 rounded-lg border border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 bg-white text-gray-800 text-sm sm:text-base transition"
      />
      <select
        v-model="filterMode"
        class="w-full max-w-full sm:w-auto px-3 sm:px-4 py-2 rounded-lg border border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 bg-white text-gray-800 text-sm sm:text-base transition"
      >
        <option value="">所有模式</option>
        <option value="synthetic">AI 生成</option>
        <option value="golden">手動標注</option>
      </select>
    </div>

    <!-- Drafts Grid -->
    <div
      v-if="filteredDrafts.length > 0"
      class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-4 gap-4 sm:gap-6"
    >
      <div
        v-for="draft in filteredDrafts"
        :key="draft.id"
        class="group bg-white shadow-lg rounded-2xl pl-3 pr-4 py-4 sm:pl-4 sm:pr-5 sm:py-5 border border-gray-100 hover:shadow-2xl hover:border-indigo-300 transition relative cursor-pointer overflow-hidden min-h-[110px] sm:min-h-[120px]"
        @click="openDraft(draft)"
      >
        <!-- 狀態色條 (z-10) -->
        <div
          :class="[
            'absolute left-0 top-0 h-full w-2 rounded-l-2xl z-10 bg-black',
            getStatusBorderColor(draft.status),
          ]"
        ></div>

        <!-- 右上角操作菜單 (z-30) -->
        <div class="absolute top-3 right-3 z-30">
          <button
            @click.stop="toggleMenu(draft.id)"
            class="text-gray-400 hover:text-indigo-600 p-1 rounded-full transition"
            title="更多操作"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-5 w-5"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <circle cx="10" cy="4" r="1.5" />
              <circle cx="10" cy="10" r="1.5" />
              <circle cx="10" cy="16" r="1.5" />
            </svg>
          </button>
          <transition name="fade">
            <div
              v-if="activeMenu === draft.id"
              class="absolute right-0 mt-2 w-36 bg-white rounded-xl shadow-xl border border-gray-100 z-40 animate-fade-in"
            >
              <ul class="py-2">
                <li>
                  <a
                    href="#"
                    @click.stop.prevent="emitRename(draft)"
                    class="block px-5 py-2 text-sm text-gray-700 hover:bg-indigo-50 rounded-md transition"
                    >重命名</a
                  >
                </li>
                <li>
                  <a
                    href="#"
                    @click.stop.prevent="emitDelete(draft)"
                    class="block px-5 py-2 text-sm text-red-600 hover:bg-red-50 rounded-md transition"
                    >刪除</a
                  >
                </li>
              </ul>
            </div>
          </transition>
        </div>

        <!-- 卡片內容 (z-20) -->
        <div
          class="flex flex-col gap-1 sm:gap-2 min-h-[90px] sm:min-h-[110px] relative z-20"
        >
          <div
            class="flex items-center gap-1 sm:gap-2 mb-0.5 sm:mb-1 pr-6 sm:pr-8"
          >
            <h3
              class="font-bold text-base sm:text-lg text-gray-800 truncate flex-1"
            >
              {{ draft.name }}
            </h3>
            <span
              class="text-[10px] sm:text-xs font-semibold px-1.5 sm:px-2 py-0.5 rounded bg-gray-100 text-gray-500 border border-gray-200 ml-1 whitespace-nowrap"
              :class="getModeTypeClass(draft.mode)"
              style="position: relative; z-index: 20"
              >{{ modeMap(draft.mode) }}</span
            >
          </div>
          <div class="flex items-center gap-1 sm:gap-2 mt-0.5 sm:mt-1">
            <span class="text-[10px] sm:text-xs font-medium text-gray-500"
              >狀態</span
            >
            <span
              :class="getStatusTextColor(draft.status)"
              class="text-[10px] sm:text-xs font-bold tracking-wide"
              >{{ getStatusText(draft.status) }}</span
            >
            <span
              v-if="draft.status === 'error'"
              class="ml-1 sm:ml-2 text-[10px] sm:text-xs text-red-500"
              >失敗</span
            >
          </div>
          <div class="text-[10px] sm:text-xs text-gray-400 mt-0.5 sm:mt-1">
            更新於 {{ new Date(draft.updated_at).toLocaleString() }}
          </div>
          <div
            v-if="
              draft.status === 'generating_idea' ||
              draft.status === 'generating_plan'
            "
            class="w-full bg-gray-200 rounded-full h-1 mt-1 sm:h-1.5 sm:mt-2"
          >
            <div
              class="bg-blue-500 h-1 rounded-full animate-pulse sm:h-1.5"
            ></div>
          </div>
        </div>
      </div>
    </div>
    <div
      v-else
      class="text-center py-8 sm:py-12 bg-white rounded-2xl shadow-lg border border-gray-100"
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        class="mx-auto h-8 w-8 sm:h-12 sm:w-12 text-gray-200 mb-2 sm:mb-3"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="1.5"
          d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
        />
      </svg>
      <p class="text-gray-400 text-sm sm:text-base">
        没有找到符合條件的計畫草稿。
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from "vue";
import {
  modeMap,
  getStatusTextColor,
  getModeTypeClass,
} from "~/utils/textMapping";

const props = defineProps({ drafts: Array });
const emit = defineEmits(["select", "rename", "delete"]);

const searchTerm = ref("");
const filterMode = ref("");
const activeMenu = ref(null);

// 切换菜单的显示/隐藏状态
function toggleMenu(draftId) {
  activeMenu.value = activeMenu.value === draftId ? null : draftId;
}

// 关闭菜单
function closeMenu() {
  activeMenu.value = null;
}

// 打开草稿，如果菜单已打开则先关闭菜单
function openDraft(draft) {
  if (activeMenu.value) {
    closeMenu();
    return;
  }
  emit("select", draft);
}

// 发送重命名事件
function emitRename(draft) {
  emit("rename", draft);
  closeMenu();
}

// 发送删除事件
function emitDelete(draft) {
  emit("delete", draft);
  closeMenu();
}

onMounted(() => {
  window.addEventListener("click", closeMenu);
});

onUnmounted(() => {
  window.removeEventListener("click", closeMenu);
});

// 计算属性：根据搜索词和过滤模式返回匹配的草稿列表
const filteredDrafts = computed(() => {
  return props.drafts.filter((draft) => {
    const nameMatch = draft.name
      .toLowerCase()
      .includes(searchTerm.value.toLowerCase());
    const modeMatch = !filterMode.value || draft.mode === filterMode.value;
    return nameMatch && modeMatch;
  });
});

// 根据草稿状态返回对应的边框颜色
function getStatusBorderColor(status) {
  const map = {
    completed: "bg-green-500",
    generating_idea: "bg-blue-500",
    generating_plan: "bg-blue-500",
    pending: "bg-gray-400",
    error: "bg-red-500",
  };
  return map[status] || "border-gray-300";
}

// 根据状态返回状态文本
function getStatusText(status) {
  const map = {
    completed: "已完成",
    generating_idea: "生成想法中...",
    generating_plan: "生成計畫中...",
    completed_idea: "已生成想法",
    pending: "待处理",
    error: "失敗",
  };
  return map[status] || status;
}
</script>

<style scoped>
/* 简单的输入框和选择框样式，可以放到全局 CSS 中 */
.input-class,
.select-class {
  @apply block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm;
}
</style>
