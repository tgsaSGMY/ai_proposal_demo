<!-- 側邊欄「關鍵指令」答案卡片：
     - 一般模式：固定高度摘要＋「展開」模態框
     - 確認模式：精簡卡片（標題＋狀態＋兩行摘要），點卡片開啟確認視窗 -->
<template>
  <div
    class="rounded-2xl border-2 transition"
    :class="[cardClass, reviewState ? 'cursor-pointer p-3 hover:shadow-md' : 'p-4']"
    :role="reviewState ? 'button' : undefined"
    :tabindex="reviewState ? 0 : undefined"
    @click="reviewState && $emit('open')"
    @keydown.enter.self="reviewState && $emit('open')"
  >
    <div class="flex items-start justify-between gap-2">
      <div class="my-auto flex min-w-0 items-center gap-2">
        <p
          class="font-semibold leading-snug tracking-[0.05em]"
          :class="[
            reviewState ? 'text-[0.9rem]' : 'text-[0.9375rem]',
            reviewState === 'confirmed' ? 'text-emerald-700' : 'text-[#ff7a5b]',
          ]"
        >
          {{ title }}
        </p>
        <span
          v-if="isAiGenerated"
          class="flex-shrink-0 rounded bg-slate-200 px-2 py-1 text-xs font-medium leading-none text-slate-600"
          :title="aiBadgeTitle"
        >
          AI
        </span>
      </div>
      <span
        v-if="reviewState"
        class="flex-shrink-0 rounded px-2 py-1 text-xs font-semibold leading-none"
        :class="
          reviewState === 'confirmed'
            ? 'bg-emerald-100 text-emerald-700'
            : 'bg-amber-100 text-amber-700'
        "
      >
        {{ reviewState === "confirmed" ? "✓ 已確認" : "待確認" }}
      </span>
    </div>

    <p
      v-overflow-fade
      :class="
        reviewState
          ? 'answer-clamp-sm mt-1.5 text-[0.8rem] leading-relaxed text-slate-500'
          : 'answer-clamp mt-2 text-sm leading-relaxed text-slate-700'
      "
    >
      <template v-if="answer">
        <span
          v-for="(segment, segIndex) in splitPlaceholders(answer)"
          :key="segIndex"
          :class="segment.hit ? 'rounded bg-amber-100 px-0.5 font-medium text-amber-800' : ''"
          >{{ segment.text }}</span
        >
      </template>
      <template v-else>（待回答）</template>
    </p>

    <div v-if="!reviewState" class="mt-3 flex items-center gap-2 border-t border-slate-200 pt-3">
      <button
        type="button"
        class="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm text-slate-700 transition hover:border-[#ff6b3d] hover:text-[#ff6b3d]"
        :title="`查看 ${title}`"
        @click="$emit('expand')"
      >
        <!-- expand icon -->
        <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4"
          />
        </svg>
        展開
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { PropType } from "vue";
import { splitPlaceholders } from "~/utils/placeholderHighlight";

const props = defineProps({
  title: { type: String, default: "" },
  answer: { type: String, default: "" },
  isAiGenerated: { type: Boolean, default: false },
  aiBadgeTitle: { type: String, default: "" },
  // 確認模式狀態；null 表示一般模式或不在確認清單
  reviewState: {
    type: String as PropType<"pending" | "confirmed" | null>,
    default: null,
  },
});

defineEmits<{
  (e: "expand"): void;
  (e: "open"): void;
}>();

const cardClass = computed(() => {
  if (props.reviewState === "confirmed") return "border-emerald-300 bg-emerald-50/40";
  if (props.reviewState === "pending") return "border-red-300 bg-slate-50";
  return "border-red-500 bg-slate-50";
});

// ===== 摘要：內容超出最大高度時才加上淡出效果 =====
const overflowObservers = new WeakMap<HTMLElement, ResizeObserver>();

function updateOverflowFade(el: HTMLElement) {
  el.classList.toggle("is-overflowing", el.scrollHeight > el.clientHeight + 1);
}

const vOverflowFade = {
  mounted(el: HTMLElement) {
    updateOverflowFade(el);
    const observer = new ResizeObserver(() => updateOverflowFade(el));
    observer.observe(el);
    overflowObservers.set(el, observer);
  },
  updated(el: HTMLElement) {
    updateOverflowFade(el);
  },
  beforeUnmount(el: HTMLElement) {
    overflowObservers.get(el)?.disconnect();
    overflowObservers.delete(el);
  },
};
</script>

<style scoped>
/* 摘要：固定高度，超出部分逐漸變灰（完整內容在「展開」模態框或確認視窗查看） */
.answer-clamp {
  max-height: 10rem;
  overflow: hidden;
}

/* 確認模式：兩行摘要，讓清單一眼看得完 */
.answer-clamp-sm {
  max-height: 2.6rem;
  overflow: hidden;
}

.answer-clamp.is-overflowing {
  -webkit-mask-image: linear-gradient(to bottom, #000 60%, rgba(0, 0, 0, 0.25) 100%);
  mask-image: linear-gradient(to bottom, #000 60%, rgba(0, 0, 0, 0.25) 100%);
}

.answer-clamp-sm.is-overflowing {
  -webkit-mask-image: linear-gradient(to bottom, #000 45%, rgba(0, 0, 0, 0.25) 100%);
  mask-image: linear-gradient(to bottom, #000 45%, rgba(0, 0, 0, 0.25) 100%);
}
</style>
