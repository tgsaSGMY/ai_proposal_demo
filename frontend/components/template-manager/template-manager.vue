<template>
  <section class="bg-white rounded-2xl shadow p-5 space-y-4">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <h2 class="text-lg font-semibold text-slate-900">模板列表</h2>
        <p class="text-xs text-slate-500">
          僅支援編輯，若需停用可把狀態改為「隱藏」
        </p>
      </div>
      <div class="flex gap-2">
        <select
          v-model="templateFilter"
          class="rounded-xl border border-slate-200 px-3 py-2 text-sm"
        >
          <option value="">全部主題</option>
          <option
            v-for="option in grantOptions"
            :key="option.value"
            :value="option.value"
          >
            {{ option.label }} ({{ option.value }})
          </option>
        </select>
        <button
          type="button"
          class="text-xs bg-rose-500 text-white px-3 py-1.5 rounded-lg font-semibold hover:bg-rose-600"
          @click="emit('new')"
        >
          新增模板
        </button>
      </div>
    </div>
    <div class="overflow-x-auto">
      <table class="min-w-full text-sm">
        <thead class="text-slate-500 text-left border-b">
          <tr>
            <th class="py-2">模板</th>
            <th class="py-2">主題</th>
            <th class="py-2">圖示色</th>
            <th class="py-2">Logo</th>
            <th class="py-2">狀態</th>
            <th class="py-2 text-right">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="template in filteredTemplates"
            :key="`${template.grant_id}-${template.id}`"
            class="border-b last:border-b-0"
          >
            <td class="py-3">
              <p class="font-semibold text-slate-900">{{ template.name }}</p>
              <p class="text-xs text-slate-500">
                {{ template.subtitle || "—" }} · ID: {{ template.id }}
              </p>
            </td>
            <td class="py-3">
              <p class="font-semibold text-slate-800">
                {{ grantNameMap.get(template.grant_id) || template.grant_id }}
              </p>
              <p class="text-xs text-slate-500">{{ template.grant_id }}</p>
            </td>
            <td class="py-3">
              <div class="flex items-center gap-2">
                <span
                  class="h-6 w-6 rounded-full border"
                  :style="{ backgroundColor: template.iconBg || '#E2E8F0' }"
                ></span>
                <span class="text-xs text-slate-600">{{
                  template.iconBg || "#E2E8F0"
                }}</span>
              </div>
            </td>
            <td class="py-3 text-center">
              <div
                v-if="template.logo_storage_path"
                class="flex items-center justify-center"
              >
                <img
                  :src="template.logo_storage_path"
                  :alt="`${template.name} Logo`"
                  class="max-h-10 max-w-10 object-contain"
                />
              </div>
              <div v-else class="text-xs text-slate-600">未設定</div>
            </td>
            <td class="py-3">
              <span
                :class="[
                  'px-3 py-1 text-xs font-semibold rounded-full',
                  template.isOpen
                    ? 'bg-emerald-50 text-emerald-600'
                    : 'bg-slate-100 text-slate-500',
                ]"
              >
                {{ template.isOpen ? "啟用" : "隱藏" }}
              </span>
            </td>
            <td class="py-3 text-right">
              <div class="flex justify-end gap-3">
                <button
                  type="button"
                  class="text-xs font-semibold text-indigo-600"
                  @click="emit('edit', template)"
                >
                  編輯
                </button>
                <button
                  type="button"
                  class="text-xs font-semibold text-slate-600 hover:text-slate-900"
                  @click="emit('sections', template)"
                >
                  調整章節
                </button>
              </div>
            </td>
          </tr>
          <tr v-if="!filteredTemplates.length">
            <td colspan="6" class="py-6 text-center text-slate-400">
              沒有符合條件的模板
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { PropType } from "vue";

interface TemplateRecord {
  id: string;
  grant_id: string;
  name: string;
  subtitle?: string | null;
  description?: string | null;
  logo_storage_path?: string | null;
  iconBg?: string | null;
  isOpen?: boolean | null;
  [key: string]: any;
}

interface GrantOption {
  label: string;
  value: string;
}

const props = defineProps({
  templates: {
    type: Array as PropType<TemplateRecord[]>,
    default: () => [],
  },
  grantOptions: {
    type: Array as PropType<GrantOption[]>,
    default: () => [],
  },
  grantNameMap: {
    type: Object as PropType<Map<string, string>>,
    default: () => new Map<string, string>(),
  },
});

const templateFilter = defineModel<string>("templateFilter", {
  required: true,
});

const filteredTemplates = computed(() => {
  if (!templateFilter.value) {
    return props.templates;
  }
  return props.templates.filter((tpl) => tpl.grant_id === templateFilter.value);
});

const emit = defineEmits<{
  (e: "edit", template: TemplateRecord): void;
  (e: "sections", template: TemplateRecord): void;
  (e: "new"): void;
}>();

defineOptions({ name: "TemplateListSection" });
</script>
