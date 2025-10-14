<template>
  <Transition name="fade">
    <div
      v-if="visible"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
    >
      <div
        class="bg-white rounded-2xl shadow-2xl w-full max-w-6xl max-h-[85vh] overflow-hidden flex flex-col"
      >
        <!-- Header -->
        <div class="flex justify-between items-center border-b p-4 bg-gray-100">
          <div>
            <h2 class="text-xl font-semibold text-gray-800">
              選擇最佳生成結果
            </h2>
            <p class="text-sm text-gray-600 mt-1">
              請為每個章節選出你要保存的版本。
            </p>
          </div>
          <div class="flex items-center gap-3">
            <button
              @click="selectAllFirst"
              class="px-3 py-1 text-sm rounded-md bg-gray-200 hover:bg-gray-300"
            >
              全選第一候選
            </button>
            <button
              @click="$emit('close')"
              class="text-gray-500 hover:text-gray-700 transition text-xl"
              aria-label="關閉"
            >
              ✕
            </button>
          </div>
        </div>

        <!-- Content -->
        <div class="flex-1 overflow-y-auto p-6 space-y-6">
          <div
            v-for="section in sections"
            :key="section.id"
            class="bg-white border rounded-xl shadow-sm p-4"
          >
            <div class="flex justify-between items-start mb-3">
              <div>
                <h3 class="font-bold text-lg text-gray-800">
                  {{ section.title || section.name || section.id }}
                </h3>
                <p
                  v-if="section.description"
                  class="text-sm text-gray-500 mt-1"
                >
                  {{ section.description }}
                </p>
              </div>
              <div class="text-sm text-gray-500">
                共 {{ (candidatePlan[section.id] || []).length }} 候選
              </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div
                v-for="(candidate, idx) in candidatePlan[section.id] || []"
                :key="idx"
                role="button"
                tabindex="0"
                class="relative border rounded-lg p-4 hover:shadow-md transition cursor-pointer bg-white"
                :class="{
                  'border-blue-500 ring-2 ring-blue-200':
                    selected[section.id] === idx,
                  'border-gray-200': selected[section.id] !== idx,
                }"
                @click="() => selectCandidate(section.id, idx)"
                @keydown.enter.prevent="() => selectCandidate(section.id, idx)"
              >
                <div class="absolute top-3 right-3">
                  <span
                    v-if="selected[section.id] === idx"
                    class="bg-blue-500 text-white text-xs px-2 py-0.5 rounded-full"
                    >已選</span
                  >
                </div>

                <div v-if="candidate.error" class="text-red-600 text-sm mb-2">
                  ⚠️ {{ candidate.error }}
                </div>

                <p
                  class="text-sm text-gray-800 whitespace-pre-wrap leading-relaxed"
                >
                  {{ candidate.content || "(無內容)" }}
                </p>

                <div
                  v-if="candidate.metadata"
                  class="mt-3 text-xs text-gray-500"
                >
                  <div v-for="(v, k) in candidate.metadata" :key="k">
                    <span class="font-medium text-gray-600">{{ k }}:</span>
                    <span> {{ String(v) }} </span>
                  </div>
                </div>
              </div>

              <!-- 當沒有任何候選時顯示提示 -->
              <div
                v-if="
                  !(
                    candidatePlan[section.id] &&
                    candidatePlan[section.id].length
                  )
                "
                class="col-span-full text-sm text-gray-500 italic p-4 border border-dashed rounded-lg"
              >
                尚無候選結果，請先產生候選。
              </div>
            </div>
          </div>
        </div>

        <!-- Footer -->
        <div
          class="border-t p-4 bg-gray-50 flex justify-between items-center gap-3"
        >
          <div class="text-sm text-gray-600">
            已為
            <span class="font-medium text-gray-800">{{ selectedCount }}</span> /
            {{ sections.length }} 個章節選擇版本
          </div>
          <div class="flex items-center gap-3">
            <button
              @click="$emit('close')"
              class="px-4 py-2 rounded-lg border border-gray-300 text-gray-600 hover:bg-gray-100"
            >
              取消
            </button>
            <button
              @click="confirmSelection"
              :disabled="!isAllSectionsSelected"
              class="px-5 py-2 rounded-lg bg-blue-600 text-white font-semibold hover:bg-blue-700 disabled:opacity-60"
            >
              確認選擇並套用
            </button>
          </div>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { reactive, computed, watch } from "vue";

const props = defineProps({
  visible: { type: Boolean, default: false },
  candidatePlan: { type: Object, required: true }, // { sectionId: [ {content, error, metadata}, ... ], ... }
  sections: { type: Array, required: true }, // [{id, title?, name?, description?}, ...]
});

const emit = defineEmits(["confirm", "close"]);

// selected: { [sectionId]: index }
const selected = reactive({});

// 每次 modal 打開時，重設或預設選擇第一個候選（若存在）
watch(
  () => props.visible,
  (v) => {
    if (v) {
      // 初始化 selected：若 candidatePlan 有候選則預設第一個
      for (const sec of props.sections) {
        const list = props.candidatePlan[sec.id];
        if (Array.isArray(list) && list.length > 0) {
          selected[sec.id] = 0;
        } else {
          // 確保沒有遺留的選擇
          if (selected[sec.id] !== undefined) delete selected[sec.id];
        }
      }
    }
  },
  { immediate: false }
);

const isAllSectionsSelected = computed(() =>
  props.sections.every((s) => selected[s.id] !== undefined)
);

const selectedCount = computed(() =>
  props.sections.reduce(
    (acc, s) => (selected[s.id] !== undefined ? acc + 1 : acc),
    0
  )
);

// 選擇某個 section 的候選索引
function selectCandidate(sectionId, idx) {
  selected[sectionId] = idx;
}

// 一鍵選第一項（方便快速操作）
function selectAllFirst() {
  for (const sec of props.sections) {
    const list = props.candidatePlan[sec.id];
    if (Array.isArray(list) && list.length > 0) selected[sec.id] = 0;
  }
}

// 將選擇的候選整理成 { sectionId: candidate } 並 emit
function confirmSelection() {
  if (!isAllSectionsSelected.value) return;
  const result = {};
  for (const sec of props.sections) {
    const idx = selected[sec.id];
    const list = props.candidatePlan[sec.id] || [];
    result[sec.id] = list[idx] ?? null;
  }
  emit("confirm", result);
  // 可選擇同時關閉 modal
  emit("close");
}
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
