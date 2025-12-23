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
          class="rounded-full border border-[#ffb4a8] px-6 py-2 text-sm font-semibold text-[#ff4b5c] hover:bg-[#fff2ef] transition"
          @click="handleExport"
        >
          下載報告 Word
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
});

const emit = defineEmits(["close", "export"]);

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
      }
    );
  } catch (error) {
    console.error("無法渲染章節", section?.id, error);
    return "";
  }
}

function handleExport() {
  emit("export", props.version);
}
</script>

<style scoped>
.prose {
  all: revert;
}
</style>
