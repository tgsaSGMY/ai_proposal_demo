<!-- 方案版本管理模态帐组件：查看計劃書版本 -->
<template>
  <div
    v-if="visible"
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
    @click.self="$emit('close')"
  >
    <div
      class="max-h-[90vh] w-full max-w-4xl overflow-y-auto rounded-[32px] bg-white shadow-2xl"
    >
      <!-- Header -->
      <div class="sticky top-0 border-b border-gray-200 bg-white px-8 py-6">
        <div class="flex items-center justify-between">
          <div>
            <p
              class="text-xs font-semibold uppercase tracking-[0.4em] text-[#ff7a5b]"
            >
              計畫推演報告
              <span class="ml-2 text-[11px] text-slate-400"
                >Plan Deduction</span
              >
            </p>
            <p class="mt-2 text-lg font-semibold text-gray-900">
              {{ version?.title || "版本詳情" }}
            </p>
            <p class="mt-1 text-xs text-slate-500">
              {{ version?.timestamp }}
            </p>
          </div>
          <button
            type="button"
            class="rounded-full hover:bg-gray-100 p-2"
            @click="$emit('close')"
          >
            <svg
              class="h-6 w-6 text-gray-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
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
      </div>

      <!-- Content -->
      <div class="space-y-4 px-8 py-6">
        <div
          v-for="section in sections"
          :key="section.id"
          class="rounded-2xl bg-[#fff7f3] px-6 py-4"
        >
          <p
            class="text-xs font-semibold uppercase tracking-[0.3em] text-[#ff8a70]"
          >
            {{ section.name }}
          </p>
          <div
            v-if="section.html"
            class="mt-3 text-sm leading-relaxed text-slate-700 prose prose-sm prose-slate"
            v-html="section.html"
          ></div>
          <p
            v-else
            class="mt-3 text-sm leading-relaxed text-slate-700 whitespace-pre-line"
          >
            {{ section.content }}
          </p>
        </div>
      </div>

      <!-- Footer -->
      <div
        class="sticky bottom-0 border-t border-gray-200 bg-white px-8 py-5 flex gap-3"
      >
        <button
          type="button"
          class="rounded-full bg-gradient-to-r from-[#ff9b6d] to-[#ff4b6b] px-6 py-2 text-sm font-semibold text-white shadow-lg shadow-[#ff4b6b]/30 disabled:cursor-not-allowed disabled:opacity-60"
          :disabled="generationLimitReached || loading || !version?.data"
          :title="generationLimitReached ? '報告生成次數已達上限，免費註冊即可繼續使用。' : ''"
          @click="handleVersionUpdate"
        >
          版本更新
        </button>
        <button
          type="button"
          class="rounded-full border border-[#ffb4a8] px-6 py-2 text-sm font-semibold text-[#ff4b5c] hover:bg-[#fff2ef] transition disabled:cursor-not-allowed disabled:opacity-60"
          :disabled="downloadLimitReached"
          :title="downloadLimitReached ? '下載次數已達上限，免費註冊即可繼續使用。' : ''"
          @click="handleExport"
        >
          下載報告
        </button>
        <button
          v-if="isInternal"
          type="button"
          class="rounded-full border border-[#ffd4c8] px-6 py-2 text-sm font-semibold text-[#ff6b5c] hover:bg-[#fff8f6] transition disabled:cursor-not-allowed disabled:opacity-60"
          :disabled="timelineLoading || !version"
          @click="handleTimelineDownload"
        >
          下載時間軸
        </button>
        <button
          type="button"
          class="rounded-full border border-gray-200 px-6 py-2 text-sm font-semibold text-gray-600 hover:bg-gray-50 transition"
          @click="$emit('close')"
        >
          關閉
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { renderPlanToHtml } from "~/utils/exportToWord";

const props = defineProps({
  visible: { type: Boolean, default: false },
  version: { type: Object, default: () => ({}) },
  planSections: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  timelineLoading: { type: Boolean, default: false },
  isInternal: { type: Boolean, default: false },
  generationLimitReached: { type: Boolean, default: false },
  downloadLimitReached: { type: Boolean, default: false },
});

const emit = defineEmits([
  "close",
  "export",
  "updateVersion",
  "downloadTimeline",
]);

// 计算属性：过滤并映射版本数据到章节列表，包含内容和HTML渲染
const sections = computed(() => {
  if (!props.version?.data || !props.planSections?.length) {
    return [];
  }

  return props.planSections
    .map((section) => {
      const versionData = props.version.data[section.id];
      if (!versionData) {
        return null;
      }

      const content = versionData.content || "";
      return {
        id: section.id,
        name: section.name,
        content,
        html: generateHtmlForSection(section, content),
      };
    })
    .filter(Boolean);
});

// 为章节内容生成HTML格式的渲染结果
function generateHtmlForSection(section, content) {
  try {
    return renderPlanToHtml(
      [
        {
          id: section.id,
          name: section.name || section.title || section.id,
          json_schema: section.json_schema,
        },
      ],
      {
        [section.id]: {
          content,
        },
      },
    );
  } catch (error) {
    console.error("無法渲染章節", section?.id, error);
    return "";
  }
}

// 触发导出事件，将版本数据发送给父组件
function handleExport() {
  emit("export", props.version);
}

// 触发版本更新事件，用新版本数据更新計畫
function handleVersionUpdate() {
  if (!props.version || !props.version.data) {
    return;
  }
  emit("updateVersion", props.version);
}

// 触发时间轴下载事件
function handleTimelineDownload() {
  if (!props.version) {
    return;
  }
  emit("downloadTimeline", props.version);
}
</script>

<style scoped>
.prose {
  all: revert;
}
</style>
