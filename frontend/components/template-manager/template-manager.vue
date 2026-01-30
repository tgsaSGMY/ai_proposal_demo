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
              <div v-if="template.logo_storage_path" class="flex items-left">
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
              <div
                ref="menuTriggers"
                :data-template-id="`${template.grant_id}-${template.id}`"
                class="inline-block"
              >
                <button
                  type="button"
                  class="p-2 rounded-lg hover:bg-slate-100 transition-colors"
                  @click="toggleMenu(`${template.grant_id}-${template.id}`)"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke-width="1.5"
                    stroke="currentColor"
                    class="size-6"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      d="M12 6.75a.75.75 0 1 1 0-1.5.75.75 0 0 1 0 1.5ZM12 12.75a.75.75 0 1 1 0-1.5.75.75 0 0 1 0 1.5ZM12 18.75a.75.75 0 1 1 0-1.5.75.75 0 0 1 0 1.5Z"
                    />
                  </svg>
                </button>
              </div>
              <Teleport to="body">
                <div
                  v-if="openMenuId === `${template.grant_id}-${template.id}`"
                  class="fixed bg-white rounded-lg shadow-lg border border-slate-200 z-50 w-48"
                  :style="
                    getMenuPosition(`${template.grant_id}-${template.id}`)
                  "
                  @click="closeMenu"
                >
                  <button
                    type="button"
                    class="block w-full text-left px-4 py-2 text-sm font-semibold text-indigo-600 hover:bg-indigo-50 first:rounded-t-lg"
                    @click="handleAction('edit', template)"
                  >
                    編輯模板
                  </button>
                  <button
                    type="button"
                    class="block w-full text-left px-4 py-2 text-sm font-semibold text-emerald-600 hover:bg-emerald-50"
                    @click="handleAction('name-config', template)"
                  >
                    名稱推薦
                  </button>
                  <button
                    type="button"
                    class="block w-full text-left px-4 py-2 text-sm font-semibold text-slate-600 hover:bg-slate-50"
                    @click="handleAction('sections', template)"
                  >
                    調整章節
                  </button>
                  <button
                    type="button"
                    class="block w-full text-left px-4 py-2 text-sm font-semibold text-rose-600 hover:bg-rose-50 last:rounded-b-lg"
                    @click="handleAction('word-editor', template)"
                  >
                    調整文檔
                  </button>
                </div>
              </Teleport>
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
import { computed, ref, nextTick } from "vue";
import type { PropType } from "vue";
import type { WordExportConfigEntry } from "~/types/wordExport";
import type { NameRecommendConfig } from "~/types/nameRecommend";

interface TemplateRecord {
  id: string;
  grant_id: string;
  name: string;
  subtitle?: string | null;
  description?: string | null;
  logo_storage_path?: string | null;
  iconBg?: string | null;
  isOpen?: boolean | null;
  word_export_config?: WordExportConfigEntry[] | null;
  name_recommend_config?: NameRecommendConfig | null;
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

const openMenuId = ref<string | null>(null);
const menuTriggers = ref<HTMLElement | null>(null);

const filteredTemplates = computed(() => {
  if (!templateFilter.value) {
    return props.templates;
  }
  return props.templates.filter((tpl) => tpl.grant_id === templateFilter.value);
});

const toggleMenu = (templateId: string) => {
  openMenuId.value = openMenuId.value === templateId ? null : templateId;
};

const closeMenu = () => {
  openMenuId.value = null;
};

const getMenuPosition = (templateId: string) => {
  // 尋找對應的菜單觸發按鈕
  const trigger = document.querySelector(
    `[data-template-id="${templateId}"]`,
  ) as HTMLElement;

  if (!trigger) {
    return { top: "0", left: "0" };
  }

  const rect = trigger.getBoundingClientRect();
  const menuHeight = 150; // 菜單的大約高度
  const menuWidth = 192; // w-48 = 12rem = 192px
  const viewportHeight = window.innerHeight;
  const viewportWidth = window.innerWidth;

  // 判斷菜單是否應該顯示在上方或下方
  const spaceBelow = viewportHeight - rect.bottom;
  const showAbove = spaceBelow < menuHeight && rect.top > menuHeight;

  // 計算頂部位置
  const top = showAbove
    ? `${rect.top - menuHeight - 8}px`
    : `${rect.bottom + 8}px`;

  // 判斷菜單是否會超出右邊界，如果會則調整為從右邊對齊
  const rightPos = viewportWidth - rect.right;
  const leftPos = rect.left - menuWidth + rect.width;

  const style: Record<string, string> = { top };

  if (rightPos >= 0 && rightPos + menuWidth <= viewportWidth) {
    style.right = `${rightPos}px`;
  } else if (leftPos >= 0) {
    style.left = `${leftPos}px`;
  } else {
    style.right = "16px"; // 如果都不行就距離右邊 16px
  }

  return style;
};

const handleAction = (action: string, template: TemplateRecord) => {
  emit(action as any, template);
  closeMenu();
};

const emit = defineEmits<{
  (e: "edit", template: TemplateRecord): void;
  (e: "sections", template: TemplateRecord): void;
  (e: "word-editor", template: TemplateRecord): void;
  (e: "name-config", template: TemplateRecord): void;
  (e: "new"): void;
}>();

defineOptions({ name: "TemplateListSection" });
</script>
