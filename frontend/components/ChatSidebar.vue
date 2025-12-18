<template>
  <div class="flex h-screen flex-col rounded-[32px] bg-white shadow-lg">
    <div class="flex-1 overflow-hidden border-b border-slate-200">
      <div class="px-5 py-4">
        <p class="text-sm font-semibold text-slate-900">想法匯總</p>
      </div>
      <div
        class="max-h-[calc(100%-56px)] space-y-3 overflow-y-auto px-5 pb-4 pr-3 scrollbar-thin scrollbar-thumb-rose-300 scrollbar-track-transparent"
      >
        <div
          v-for="item in qaItems"
          :key="item.id"
          class="rounded-2xl bg-slate-50 p-3"
        >
          <p
            class="text-xs font-semibold uppercase tracking-[0.3em] text-[#ff7a5b]"
          >
            {{ item.questionLabel }}
          </p>
          <p class="mt-2 text-xs text-slate-600 line-clamp-2">
            {{ item.answer || "（待回答）" }}
          </p>
        </div>
        <div v-if="!qaItems.length" class="py-6 text-center">
          <p class="text-xs text-slate-400">尚無詢問記錄</p>
        </div>
      </div>
    </div>

    <div class="flex-1 overflow-hidden">
      <div class="px-5 py-4">
        <p class="text-sm font-semibold text-slate-900">版本記錄</p>
      </div>
      <div
        class="max-h-[calc(100%-56px)] space-y-2 overflow-y-auto px-5 pb-4 pr-3 scrollbar-thin scrollbar-thumb-rose-300 scrollbar-track-transparent"
      >
        <div
          v-for="version in versions"
          :key="version.id"
          class="flex items-start gap-2 rounded-2xl bg-slate-50 p-3 text-left"
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
        </div>
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
  guidedQuestions: {
    type: Array,
    default: () => [],
  },
});

const qaItems = computed(() => {
  const items: QAItem[] = [];

  (props.guidedQuestions || []).forEach((question: any) => {
    const answer = props.questionAnswers?.[question.id] || "";
    items.push({
      id: question.id,
      questionLabel: question.label || question.prompt || "問題",
      answer: answer,
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

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
