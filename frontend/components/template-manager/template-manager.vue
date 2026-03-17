<!-- 模板管理 -->
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
          :disabled="props.loading"
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
          :disabled="props.loading"
          :class="props.loading ? 'cursor-not-allowed opacity-70' : ''"
          @click="emit('new')"
        >
          新增模板
        </button>
      </div>
    </div>
    <p class="text-xs text-slate-400">
      {{
        props.loading
          ? "模板更新中，請稍候..."
          : "切換為「全部主題」時可拖曳調整模板順序。"
      }}
    </p>
    <div class="relative overflow-x-auto">
      <div
        v-if="props.loading"
        class="absolute inset-0 z-20 flex items-center justify-center bg-white/60 backdrop-blur-[1px]"
      >
        <p
          class="rounded-full bg-white px-4 py-1.5 text-xs font-semibold text-slate-600 shadow"
        >
          更新模板順序中...
        </p>
      </div>
      <table class="min-w-full text-sm">
        <thead class="text-slate-500 text-left border-b">
          <tr>
            <th class="py-2">模板</th>
            <th class="py-2">主題</th>
            <th class="py-2">付費方案</th>
            <th class="py-2">送件截止日期</th>
            <th class="py-2 min-w-[220px]">最高補助額</th>
            <th class="py-2">圖示色</th>
            <th class="py-2">Logo</th>
            <th class="py-2">狀態</th>
            <th class="py-2 text-right">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(template, index) in filteredTemplates"
            :key="`${template.grant_id}-${template.id}`"
            class="border-b last:border-b-0"
            :class="[
              canDragReorder ? 'cursor-move' : '',
              dragOverTemplateIndex === index ? 'bg-indigo-50' : '',
            ]"
            :draggable="canDragReorder"
            @dragstart="startDragTemplate(index, $event)"
            @dragover="dragOverTemplate(index, $event)"
            @drop="dropTemplate(index, $event)"
            @dragend="dragEndTemplate"
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
              <span
                :class="[
                  'px-3 py-1 text-xs font-semibold rounded-full',
                  template.requires_paid_plan !== false
                    ? 'bg-amber-50 text-amber-700'
                    : 'bg-emerald-50 text-emerald-700',
                ]"
              >
                {{ template.requires_paid_plan !== false ? "需要" : "不需要" }}
              </span>
            </td>
            <td class="py-3 text-slate-700 text-sm">
              {{ template.submission_deadline || "—" }}
            </td>
            <td class="py-3 min-w-[220px] text-slate-700 text-sm">
              <p class="max-w-[320px] whitespace-normal break-words">
                {{ template.subsidy_amount || "—" }}
              </p>
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
                  :disabled="props.loading"
                  :class="props.loading ? 'cursor-not-allowed opacity-60' : ''"
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
                  class="fixed inset-0 z-40"
                  @click="closeMenu"
                ></div>
                <div
                  v-if="openMenuId === `${template.grant_id}-${template.id}`"
                  class="absolute bg-white rounded-lg shadow-lg border border-slate-200 z-50 w-48"
                  :style="
                    getMenuPosition(`${template.grant_id}-${template.id}`)
                  "
                  @click.stop
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
            <td colspan="9" class="py-6 text-center text-slate-400">
              沒有符合條件的模板
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, nextTick, onMounted, onBeforeUnmount } from "vue";
import type { PropType } from "vue";
import type { WordExportConfigEntry } from "~/types/wordExport";
import type { NameRecommendConfig } from "~/types/nameRecommend";

// 模板資料結構，兼容後端擴充欄位。
interface TemplateRecord {
  id: string;
  grant_id: string;
  order?: number | null;
  name: string;
  requires_paid_plan?: boolean | null;
  submission_deadline?: string | null;
  subsidy_amount?: string | null;
  subtitle?: string | null;
  description?: string | null;
  logo_storage_path?: string | null;
  iconBg?: string | null;
  isOpen?: boolean | null;
  word_export_config?: WordExportConfigEntry[] | null;
  name_recommend_config?: NameRecommendConfig | null;
  [key: string]: any;
}

// 主題下拉選單的顯示資料。
interface GrantOption {
  label: string;
  value: string;
}

// 接收模板資料、主題選項、主題名稱映射與載入狀態。
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
  loading: {
    type: Boolean,
    default: false,
  },
});

// 與父層同步目前主題篩選值。
const templateFilter = defineModel<string>("templateFilter", {
  required: true,
});

// 控制操作選單、拖曳狀態與拖曳目標索引。
const openMenuId = ref<string | null>(null);
const menuTriggers = ref<HTMLElement | null>(null);
const draggedTemplateIndex = ref<number | null>(null);
const dragOverTemplateIndex = ref<number | null>(null);

// 只有在「全部主題」且非 loading 時允許拖曳排序。
const isAllThemesSelected = computed(() => !templateFilter.value);
const canDragReorder = computed(
  () => isAllThemesSelected.value && !props.loading,
);

// 將 order 轉成可排序數字；無效值一律放到最後。
function getTemplateOrderValue(template: TemplateRecord) {
  const numeric = Number(template.order);
  return Number.isFinite(numeric) && numeric > 0
    ? numeric
    : Number.MAX_SAFE_INTEGER;
}

// 模板排序規則：order -> grant_id -> name。
function sortTemplates(list: TemplateRecord[]) {
  return [...list].sort((a, b) => {
    const orderDiff = getTemplateOrderValue(a) - getTemplateOrderValue(b);
    if (orderDiff !== 0) {
      return orderDiff;
    }
    const grantDiff = (a.grant_id || "").localeCompare(b.grant_id || "");
    if (grantDiff !== 0) {
      return grantDiff;
    }
    return (a.name || "").localeCompare(b.name || "");
  });
}

// 依主題篩選後回傳排序結果，確保顯示順序穩定。
const filteredTemplates = computed(() => {
  if (!templateFilter.value) {
    return sortTemplates(props.templates);
  }
  return sortTemplates(
    props.templates.filter((tpl) => tpl.grant_id === templateFilter.value),
  );
});

// 開始拖曳時記錄來源索引，並設定 drag 效果。
function startDragTemplate(index: number, event: DragEvent) {
  if (!canDragReorder.value) {
    return;
  }
  draggedTemplateIndex.value = index;
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = "move";
  }
}

// 拖曳經過目標列時更新高亮索引。
function dragOverTemplate(index: number, event: DragEvent) {
  if (!canDragReorder.value || draggedTemplateIndex.value === null) {
    return;
  }
  event.preventDefault();
  if (event.dataTransfer) {
    event.dataTransfer.dropEffect = "move";
  }
  dragOverTemplateIndex.value = index;
}

// 完成拖放後重新計算順序並回傳給父層持久化。
function dropTemplate(index: number, event: DragEvent) {
  if (!canDragReorder.value) {
    return;
  }
  event.preventDefault();
  dragOverTemplateIndex.value = null;

  if (draggedTemplateIndex.value === null) {
    return;
  }

  const sourceIndex = draggedTemplateIndex.value;
  draggedTemplateIndex.value = null;
  if (sourceIndex === index) {
    return;
  }

  const reordered = [...filteredTemplates.value];
  const [movedTemplate] = reordered.splice(sourceIndex, 1);
  if (!movedTemplate) {
    return;
  }
  reordered.splice(index, 0, movedTemplate);

  const payload = reordered.map((template, idx) => ({
    id: template.id,
    grant_id: template.grant_id,
    order: idx + 1,
  }));
  emit("reorder", payload);
}

// 清理拖曳暫存狀態。
function dragEndTemplate() {
  draggedTemplateIndex.value = null;
  dragOverTemplateIndex.value = null;
}

// 頁面捲動時自動關閉選單，避免定位偏移造成誤點。
onMounted(() => {
  const handleScroll = () => {
    if (openMenuId.value) {
      openMenuId.value = null;
    }
  };
  window.addEventListener("scroll", handleScroll);
  onBeforeUnmount(() => {
    window.removeEventListener("scroll", handleScroll);
  });
});

// 切換指定模板的更多操作選單。
const toggleMenu = (templateId: string) => {
  if (props.loading) {
    return;
  }
  openMenuId.value = openMenuId.value === templateId ? null : templateId;
};

// 關閉目前展開的操作選單。
const closeMenu = () => {
  openMenuId.value = null;
};

// 計算操作選單在視窗中的定位，避免超出可視範圍。
const getMenuPosition = (templateId: string) => {
  // 尋找對應的菜單觸發按鈕。
  const trigger = document.querySelector(
    `[data-template-id="${templateId}"]`,
  ) as HTMLElement;

  if (!trigger) {
    return { top: "0", left: "0" };
  }

  const rect = trigger.getBoundingClientRect();
  const scrollY = window.scrollY || window.pageYOffset;
  const scrollX = window.scrollX || window.pageXOffset;

  const menuHeight = 150; // 菜單的大約高度
  const menuWidth = 192; // w-48 = 12rem = 192px
  const viewportHeight = window.innerHeight;
  const viewportWidth = window.innerWidth;

  // 判斷菜單是否應該顯示在上方或下方。
  const spaceBelow = viewportHeight - rect.bottom;
  const showAbove = spaceBelow < menuHeight && rect.top > menuHeight;

  // 計算相對於文檔（考慮滾動）的頂部位置。
  const top = showAbove
    ? `${rect.top + scrollY - menuHeight - 8}px`
    : `${rect.top + scrollY + rect.height + 8}px`;

  // 計算左側位置。
  const rightPos = viewportWidth - rect.right;
  const leftPos = rect.left - menuWidth + rect.width;

  const style: Record<string, string> = { top };

  if (rightPos >= 0 && rightPos + menuWidth <= viewportWidth) {
    style.right = `${rightPos}px`;
  } else if (leftPos >= 0) {
    style.left = `${leftPos + scrollX}px`;
  } else {
    style.right = "16px"; // 若無法左右對齊，退回固定右側間距。
  }

  return style;
};

// 點擊功能選單後派發對應事件並關閉選單。
const handleAction = (action: string, template: TemplateRecord) => {
  emit(action as any, template);
  closeMenu();
};

// 對外事件：模板操作與拖曳排序結果。
const emit = defineEmits<{
  (e: "edit", template: TemplateRecord): void;
  (e: "sections", template: TemplateRecord): void;
  (e: "word-editor", template: TemplateRecord): void;
  (e: "name-config", template: TemplateRecord): void;
  (
    e: "reorder",
    templates: Array<{ id: string; grant_id: string; order: number }>,
  ): void;
  (e: "new"): void;
}>();

// 提供元件名稱，方便 Vue DevTools 與錯誤追蹤辨識。
defineOptions({ name: "TemplateListSection" });
</script>
