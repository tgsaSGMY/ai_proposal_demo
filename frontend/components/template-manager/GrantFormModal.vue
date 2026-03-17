<!-- 主題表單彈窗 -->
<template>
  <div
    v-if="isVisible"
    class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-40"
    @click.self="emit('cancel')"
  >
    <section
      class="bg-white rounded-2xl shadow p-5 sm:p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto space-y-4"
    >
      <div class="flex items-center justify-between mb-2">
        <div>
          <h2 class="text-lg font-semibold text-slate-900">
            {{ grantFormMode === "create" ? "新增主題" : "編輯主題" }}
          </h2>
          <p class="text-xs text-slate-500">輸入 Grant ID 與對應顯示名稱</p>
        </div>
        <button
          type="button"
          class="text-2xl font-bold text-slate-400 hover:text-slate-600"
          @click="emit('cancel')"
        >
          ×
        </button>
      </div>
      <form class="space-y-4" @submit.prevent="emit('submit')">
        <label class="block space-y-1">
          <span class="text-sm font-medium text-slate-700"
            >主题ID（只能包含英文字母、数字和下划线）</span
          >
          <input
            v-model="grantForm.id"
            type="text"
            class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:border-rose-400"
            placeholder="例如：marketing"
            :readonly="grantFormMode === 'edit'"
          />
        </label>
        <label class="block space-y-1">
          <span class="text-sm font-medium text-slate-700">顯示名稱</span>
          <input
            v-model="grantForm.name"
            type="text"
            class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:border-rose-400"
            placeholder="例如：行銷型"
          />
        </label>
        <div class="flex gap-3 pt-4">
          <button
            type="button"
            class="flex-1 rounded-xl bg-slate-200 text-slate-700 py-2 text-sm font-semibold hover:bg-slate-300"
            @click="emit('cancel')"
          >
            取消
          </button>
          <button
            type="submit"
            class="flex-1 rounded-xl bg-slate-900 text-white py-2 text-sm font-semibold tracking-wide disabled:opacity-50"
            :disabled="saving"
          >
            {{ grantFormMode === "create" ? "新增" : "更新" }}
          </button>
        </div>
      </form>
    </section>
  </div>
</template>

<script setup lang="ts">
import type { PropType } from "vue";

// 主題資料型別，保留擴充欄位避免未來新增欄位造成型別衝突。
interface GrantRecord {
  id: string;
  name: string;
  [key: string]: any;
}

// 表單僅維護主題 ID 與顯示名稱兩個欄位。
interface GrantFormState {
  id: string;
  name: string;
}

// 控制彈窗顯示、模式（新增/編輯）與儲存中狀態。
const props = defineProps({
  isVisible: {
    type: Boolean,
    default: false,
  },
  grantFormMode: {
    type: String as PropType<"create" | "edit">,
    default: "create",
  },
  saving: {
    type: Boolean,
    default: false,
  },
});

// 與父層雙向綁定主題表單狀態。
const grantForm = defineModel<GrantFormState>("grantForm", {
  required: true,
});

// 對外提供提交與取消事件。
const emit = defineEmits<{
  (e: "submit"): void;
  (e: "cancel"): void;
}>();

// 提供元件名稱，方便 Vue DevTools 與錯誤追蹤辨識。
defineOptions({ name: "GrantFormModal" });
</script>
