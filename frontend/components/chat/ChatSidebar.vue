<!-- 聊天侧边栏组件：显示聊天關鍵指令和版本歷史 -->
<template>
  <div class="flex h-screen flex-col rounded-[32px] bg-white shadow-lg">
    <div class="flex-[0.7] overflow-hidden border-b border-slate-200">
      <div class="px-5 py-4">
        <p class="text-sm font-semibold text-slate-900">關鍵指令</p>
      </div>
      <div
        class="max-h-[calc(100%-56px)] space-y-3 overflow-y-auto px-5 pb-4 pr-3 scrollbar-thin scrollbar-thumb-rose-300 scrollbar-track-transparent"
      >
        <div
          v-for="item in qaItems"
          :key="item.id"
          class="rounded-2xl bg-slate-50 p-3 border-2 border-red-500"
        >
          <div class="flex items-start justify-between">
            <p
              class="text-xs font-semibold uppercase tracking-[0.3em] text-[#ff7a5b] my-auto"
            >
              {{ item.questionLabel }}
            </p>
            <button
              type="button"
              class="ml-2 inline-flex items-center justify-center rounded-md p-2 text-[#ff6b3d] bg-[#fff1ea] hover:bg-[#ffefea] shadow-sm"
              :title="`編輯 ${item.questionLabel}`"
              @click="
                $emit('editQuestion', {
                  questionId: item.id,
                  questionLabel: item.questionLabel,
                  answer: item.answer,
                })
              "
            >
              <!-- pencil icon -->
              <svg
                xmlns="http://www.w3.org/2000/svg"
                class="h-5 w-5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                stroke-width="2"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  d="M15.232 5.232l3.536 3.536M4 20h4.586a1 1 0 00.707-.293l9.414-9.414a1 1 0 000-1.414l-3.293-3.293a1 1 0 00-1.414 0L4.293 15.293A1 1 0 004 15.999V20z"
                />
              </svg>
            </button>
          </div>
          <p class="mt-2 text-xs text-slate-600">
            {{ item.answer || "（待回答）" }}
          </p>
        </div>
        <div v-if="!qaItems.length" class="py-6 text-center">
          <p class="text-xs text-slate-400">尚無詢問記錄</p>
        </div>
      </div>
    </div>

    <div class="flex-[0.3] overflow-hidden">
      <div class="px-5 py-4">
        <p class="text-sm font-semibold text-slate-900">版本記錄</p>
      </div>
      <div
        class="max-h-[calc(100%-56px)] space-y-2 overflow-y-auto px-5 pb-4 pr-3 scrollbar-thin scrollbar-thumb-rose-300 scrollbar-track-transparent"
      >
        <button
          v-for="version in versions"
          :key="version.id"
          type="button"
          class="w-full flex items-start gap-2 rounded-2xl bg-slate-50 p-3 text-left transition hover:bg-slate-100 hover:shadow-md"
          @click="$emit('selectVersion', version)"
        >
          <span
            class="mt-0.5 inline-flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full bg-[#fff1ea] text-xs font-semibold text-[#ff6b3d]"
          >
            {{ version.number }}
          </span>
          <div class="min-w-0 flex-1">
            <p class="text-xs font-semibold text-slate-800">
              {{ version.title }}
            </p>
            <p class="mt-1 text-[11px] text-slate-500">
              {{ version.timestamp }}
            </p>
          </div>
        </button>
        <div v-if="!versions.length" class="py-6 text-center">
          <p class="text-xs text-slate-400">尚無版本記錄</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

interface QAItem {
  id: string;
  questionLabel: string;
  answer: string;
  updatedAt?: string;
}

interface VersionRecord {
  id: string;
  number: number;
  title: string;
  timestamp: string;
}

const props = defineProps({
  messages: {
    type: Array,
    default: () => [],
  },
  versions: {
    type: Array as () => VersionRecord[],
    default: () => [],
  },
  questionAnswers: {
    type: Object as () => Record<string, string>,
    default: () => {},
  },
  questionAnswerMeta: {
    type: Object as () => Record<string, { updated_at?: string }>,
    default: () => ({}),
  },
});

const emit = defineEmits(["selectVersion", "editQuestion"]);

// 計算屬性：將問題答案轉換為顯示格式，支持按中文數字排序和提取 Label
const qaItems = computed(() => {
  const items: QAItem[] = [];
  const answers = props.questionAnswers || {};
  const metaMap = props.questionAnswerMeta || {};

  // 中文数字顺序映射
  const chineseNumberOrder: Record<string, number> = {
    一: 1,
    二: 2,
    三: 3,
    四: 4,
    五: 5,
    六: 6,
    七: 7,
    八: 8,
    九: 9,
    十: 10,
  };

  // 先提取所有key-value对，计算label
  const tempItems: Array<{
    key: string;
    label: string;
    answer: string;
    updatedAt?: string;
  }> = [];

  Object.entries(answers).forEach(([key, value]) => {
    const answer = String(value || "").trim();
    if (answer) {
      // 提取label：保留第一個"::"之前的所有文字（通常為章節名稱）
      let label = key;
      const firstDoubleColonIndex = key.indexOf("::");
      if (firstDoubleColonIndex !== -1) {
        label = key.substring(0, firstDoubleColonIndex);
      }

      const meta = metaMap[key] || {};
      const updatedAt = meta.updated_at || "";
      tempItems.push({ key, label, answer, updatedAt });
    }
  });

  tempItems.sort((a, b) => {
    const aTime = a.updatedAt ? Date.parse(a.updatedAt) || 0 : 0;
    const bTime = b.updatedAt ? Date.parse(b.updatedAt) || 0 : 0;
    if (aTime !== bTime) {
      return bTime - aTime;
    }
    const aFirstChar = a.label.charAt(0);
    const bFirstChar = b.label.charAt(0);
    const aOrder = chineseNumberOrder[aFirstChar] ?? 999;
    const bOrder = chineseNumberOrder[bFirstChar] ?? 999;
    if (aOrder !== bOrder) {
      return aOrder - bOrder;
    }
    return a.label.localeCompare(b.label, "zh-Hant");
  });

  // 排序后再push到items
  tempItems.forEach(({ key, label, answer, updatedAt }) => {
    items.push({
      id: key,
      questionLabel: label,
      answer: answer,
      updatedAt,
    });
  });

  return items;
});
</script>

<style scoped>
.scrollbar-thin::-webkit-scrollbar {
  width: 6px;
}

.scrollbar-thumb-rose-300::-webkit-scrollbar-thumb {
  background-color: #ffb4a8;
  border-radius: 3px;
}

.scrollbar-thumb-rose-300::-webkit-scrollbar-thumb:hover {
  background-color: #ff998e;
}

.scrollbar-track-transparent::-webkit-scrollbar-track {
  background-color: transparent;
  border-radius: 3px;
}

.scrollbar-thin {
  scrollbar-width: thin;
  scrollbar-color: #ffb4a8 transparent;
}
</style>
