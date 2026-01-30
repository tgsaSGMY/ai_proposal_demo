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
          <span class="text-sm font-medium text-slate-700">Grant ID</span>
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

interface GrantRecord {
  id: string;
  name: string;
  [key: string]: any;
}

interface GrantFormState {
  id: string;
  name: string;
}

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

const grantForm = defineModel<GrantFormState>("grantForm", {
  required: true,
});

const emit = defineEmits<{
  (e: "submit"): void;
  (e: "cancel"): void;
}>();

defineOptions({ name: "GrantFormModal" });
</script>
