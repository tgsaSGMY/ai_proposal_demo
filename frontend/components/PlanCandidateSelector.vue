<template>
  <Transition name="fade">
    <div
      v-if="visible"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
    >
      <div
        class="bg-white rounded-2xl shadow-2xl w-full max-w-lg sm:max-w-2xl md:max-w-4xl lg:max-w-6xl max-h-[85vh] overflow-hidden flex flex-col"
      >
        <!-- Header -->
        <div
          class="flex flex-col sm:flex-row justify-between items-stretch sm:items-center border-b p-3 sm:p-4 bg-gray-100 gap-2 sm:gap-0"
        >
          <div>
            <h2 class="text-base sm:text-xl font-semibold text-gray-800">
              選擇最佳生成結果
            </h2>
            <p class="text-xs sm:text-sm text-gray-600 mt-1">
              請為每個章節選出你要保存的版本。
            </p>
          </div>
          <div class="flex items-center gap-2 sm:gap-3">
            <button
              @click="selectAllFirst"
              class="px-2 sm:px-3 py-1 text-xs sm:text-sm rounded-md bg-gray-200 hover:bg-gray-300"
            >
              全選第一候選
            </button>
            <button
              @click="$emit('close')"
              class="text-gray-500 hover:text-gray-700 transition text-lg sm:text-xl"
              aria-label="關閉"
            >
              ✕
            </button>
          </div>
        </div>

        <!-- Content -->
        <div class="flex-1 overflow-y-auto p-3 sm:p-6 space-y-4 sm:space-y-6">
          <div
            v-for="section in sections"
            :key="section.id"
            class="bg-white border rounded-xl shadow-sm p-3 sm:p-4"
          >
            <div
              class="flex flex-col sm:flex-row justify-between items-stretch sm:items-start mb-2 sm:mb-3 gap-1 sm:gap-0"
            >
              <div>
                <h3 class="font-bold text-base sm:text-lg text-gray-800">
                  {{ section.title || section.name || section.id }}
                </h3>
                <p
                  v-if="section.description"
                  class="text-xs sm:text-sm text-gray-500 mt-1"
                >
                  {{ section.description }}
                </p>
              </div>
              <div class="text-xs sm:text-sm text-gray-500">
                共 {{ (candidatePlan[section.id] || []).length }} 候選
              </div>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
              <div
                v-for="(candidate, idx) in candidatePlan[section.id] || []"
                :key="idx"
                role="button"
                tabindex="0"
                class="relative border rounded-lg p-3 sm:p-4 hover:shadow-md transition cursor-pointer bg-white text-xs sm:text-sm"
                :class="{
                  'border-blue-500 ring-2 ring-blue-200':
                    selected[section.id] === idx,
                  'border-gray-200': selected[section.id] !== idx,
                }"
                @click="() => selectCandidate(section.id, idx)"
                @keydown.enter.prevent="() => selectCandidate(section.id, idx)"
              >
                <div class="absolute top-2 right-2 sm:top-3 sm:right-3">
                  <span
                    v-if="selected[section.id] === idx"
                    class="bg-blue-500 text-white text-xs px-2 py-0.5 rounded-full"
                    >已選</span
                  >
                </div>

                <div
                  v-if="candidate.error"
                  class="text-red-600 text-xs sm:text-sm mb-2"
                >
                  ⚠️ {{ candidate.error }}
                </div>

                <div
                  class="prose max-w-none text-xs sm:text-sm text-gray-800 whitespace-pre-wrap leading-relaxed"
                  v-html="generateHtmlForCandidate(section, candidate.content)"
                ></div>

                <div
                  v-if="candidate.metadata"
                  class="mt-2 sm:mt-3 text-[10px] sm:text-xs text-gray-500"
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
                class="col-span-full text-xs sm:text-sm text-gray-500 italic p-3 sm:p-4 border border-dashed rounded-lg"
              >
                尚無候選結果，請先產生候選。
              </div>
            </div>
          </div>
        </div>

        <!-- Footer -->
        <div
          class="border-t p-3 sm:p-4 bg-gray-50 flex flex-col sm:flex-row justify-between items-stretch sm:items-center gap-2 sm:gap-3"
        >
          <div class="text-xs sm:text-sm text-gray-600">
            已為
            <span class="font-medium text-gray-800">{{ selectedCount }}</span> /
            {{ sections.length }} 個章節選擇版本
          </div>
          <div class="flex items-center gap-2 sm:gap-3">
            <button
              @click="$emit('close')"
              class="px-3 sm:px-4 py-2 rounded-lg border border-gray-300 text-gray-600 hover:bg-gray-100 text-xs sm:text-base"
            >
              取消
            </button>
            <button
              @click="confirmSelection"
              :disabled="!isAllSectionsSelected"
              class="px-4 sm:px-5 py-2 rounded-lg bg-blue-600 text-white font-semibold hover:bg-blue-700 disabled:opacity-60 text-xs sm:text-base"
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
import { renderPlanToHtml } from "~/utils/exportToWord";

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

function confirmSelection() {
  const finalSelected = {};
  const finalRejected = {}; // 用不同的变量名以避免与 props.selected 冲突

  // 我们应该遍历 sections prop 来确保覆盖所有显示的 section
  for (const section of props.sections) {
    const sectionId = section.id;
    const candidates = props.candidatePlan[sectionId];

    // 从 reactive 的 selected 对象中获取用户选择的索引
    const selectedIndex = selected[sectionId];

    // 确保该 section 有候选方案并且用户已做出选择
    if (
      candidates &&
      Array.isArray(candidates) &&
      selectedIndex !== undefined
    ) {
      // 检查索引是否有效
      if (candidates[selectedIndex]) {
        // 将选中的方案放入 finalSelected
        finalSelected[sectionId] = candidates[selectedIndex];

        // 找出被拒绝的方案，仅在有2个候选方案时有效
        if (candidates.length === 2) {
          const rejectedIndex = 1 - selectedIndex; // 0 -> 1, 1 -> 0
          if (candidates[rejectedIndex]) {
            finalRejected[sectionId] = candidates[rejectedIndex];
          }
        }
      }
    }
  }

  // 发出包含选中和被拒绝方案的事件
  emit("confirm", { selected: finalSelected, rejected: finalRejected });

  emit("close"); // 您可以决定是在确认后自动关闭，还是让父组件来控制
}

function generateHtmlForCandidate(section, candidateContent) {
  if (!section || !section.id || !candidateContent) {
    return '<p class="text-gray-500 italic">（無內容）</p>';
  }

  const singleSectionArray = [
    {
      id: section.id,
      name: section.title || section.name || section.id,
      json_schema: section.json_schema,
    },
  ];

  const formattedPlanContent = {
    [section.id]: {
      content: candidateContent,
    },
  };

  return renderPlanToHtml(singleSectionArray, formattedPlanContent);
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
