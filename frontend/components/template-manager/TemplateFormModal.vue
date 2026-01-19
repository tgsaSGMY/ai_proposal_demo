<template>
  <div
    v-if="isVisible"
    class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-40"
    @click.self="emit('cancel')"
  >
    <section
      class="bg-white rounded-2xl shadow p-5 sm:p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto space-y-4"
    >
      <div class="flex flex-wrap items-center justify-between gap-3 mb-2">
        <div>
          <h2 class="text-lg font-semibold text-slate-900">
            {{ templateFormMode === "create" ? "新增模板" : "編輯模板" }}
          </h2>
          <p class="text-xs text-slate-500">設定模板基本資訊與視覺元素</p>
        </div>
        <button
          type="button"
          class="text-2xl font-bold text-slate-400 hover:text-slate-600"
          @click="emit('cancel')"
        >
          ×
        </button>
      </div>
      <form class="grid gap-4 md:grid-cols-2" @submit.prevent="emit('submit')">
        <label class="block space-y-1">
          <span class="text-sm font-medium text-slate-700">隸屬主題</span>
          <select
            v-model="templateForm.grant_id"
            class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:border-rose-400"
          >
            <option value="" disabled>請先選擇</option>
            <option
              v-for="option in grantOptions"
              :key="option.value"
              :value="option.value"
            >
              {{ option.label }} ({{ option.value }})
            </option>
          </select>
        </label>
        <label class="block space-y-1">
          <span class="text-sm font-medium text-slate-700">模板ID</span>
          <input
            v-model="templateForm.id"
            type="text"
            class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:border-rose-400"
            placeholder="例如：imdp"
            :readonly="templateFormMode === 'edit'"
          />
        </label>
        <label class="block space-y-1">
          <span class="text-sm font-medium text-slate-700">模板名稱</span>
          <input
            v-model="templateForm.name"
            type="text"
            class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:border-rose-400"
            placeholder="例如：IMDP"
          />
        </label>
        <label class="block space-y-1">
          <span class="text-sm font-medium text-slate-700">副標</span>
          <input
            v-model="templateForm.subtitle"
            type="text"
            class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:border-rose-400"
            placeholder="簡短描述"
          />
        </label>
        <label class="block space-y-1 md:col-span-2">
          <span class="text-sm font-medium text-slate-700">描述</span>
          <textarea
            v-model="templateForm.description"
            rows="3"
            class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:border-rose-400"
            placeholder="補助計畫說明"
          ></textarea>
        </label>
        <div
          class="md:col-span-2 flex flex-wrap items-center gap-2 rounded-xl bg-slate-50 px-4 py-3 text-xs text-slate-600"
        >
          <span class="font-medium text-slate-700">Logo Storage Path</span>
          <span class="font-mono text-slate-500">
            {{
              templateForm.id
                ? "logos/" + templateForm.id + "_logo.png"
                : "logos/{template_id}_logo.png"
            }}
          </span>
          <span class="text-[11px] text-slate-400">
            * 系統會依照模板 ID 自動生成路徑
          </span>
        </div>
        <label class="block space-y-2 md:col-span-2">
          <span class="text-sm font-medium text-slate-700">Icon 背景色</span>
          <div
            class="flex flex-col gap-3 rounded-xl border border-slate-200 p-4"
          >
            <div class="flex flex-wrap items-center gap-2">
              <input
                v-model="templateForm.iconBg"
                type="text"
                class="flex-1 min-w-[180px] rounded-xl border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:border-rose-400"
                placeholder="#fef3f2"
              />
              <span
                class="h-10 w-10 rounded-xl border"
                :style="{ backgroundColor: templateForm.iconBg || '#F8FAFC' }"
              ></span>
            </div>
            <color-picker-block
              v-model="templateForm.iconBg"
              with-hex-input
              :with-colors-history="6"
              class="rounded-xl bg-white"
            />
          </div>
        </label>
        <label
          class="flex items-center gap-2 text-sm font-medium text-slate-700"
        >
          <input
            type="checkbox"
            v-model="templateForm.isOpen"
            class="h-4 w-4 rounded border-slate-300"
          />
          顯示於前臺
        </label>
        <div class="md:col-span-2">
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
              class="flex-1 rounded-xl bg-rose-500 text-white py-2 text-sm font-semibold tracking-wide disabled:opacity-50"
              :disabled="templateSaving || !templateForm.grant_id"
            >
              {{ templateFormMode === "create" ? "新增" : "更新" }}
            </button>
          </div>
        </div>
      </form>
    </section>
  </div>
</template>

<script setup lang="ts">
import type { PropType } from "vue";

interface TemplateFormState {
  id: string;
  grant_id: string;
  name: string;
  subtitle: string;
  description: string;
  logo_storage_path: string;
  iconBg: string;
  isOpen: boolean;
}

interface GrantOption {
  label: string;
  value: string;
}

const props = defineProps({
  isVisible: {
    type: Boolean,
    default: false,
  },
  grantOptions: {
    type: Array as PropType<GrantOption[]>,
    default: () => [],
  },
  templateFormMode: {
    type: String as PropType<"create" | "edit">,
    default: "create",
  },
  templateSaving: {
    type: Boolean,
    default: false,
  },
});

const templateForm = defineModel<TemplateFormState>("templateForm", {
  required: true,
});

const emit = defineEmits<{
  (e: "submit"): void;
  (e: "cancel"): void;
}>();

defineOptions({ name: "TemplateFormModal" });
</script>
