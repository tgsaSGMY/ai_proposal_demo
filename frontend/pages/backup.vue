<template>
  <div class="min-h-screen bg-slate-100">
    <div class="max-w-full mx-auto space-y-6">
      <section
        v-if="currentStage === 1"
        class="bg-white rounded-3xl p-6 sm:p-8 shadow-lg flex flex-col gap-5"
      >
        <header class="flex justify-between items-start gap-5 flex-wrap">
          <div>
            <p class="text-xs uppercase tracking-widest text-indigo-600">
              第一階段 · 準備資料
            </p>
            <h2 class="text-2xl sm:text-3xl font-bold text-slate-900 mt-1">
              選擇補助並可匯入參考檔案
            </h2>
            <p class="text-sm sm:text-base text-slate-600 mt-1">
              先鎖定補助與模板，再視需要匯入 Word / Excel 作為背景，完成後即可
              前往參考連結階段。
            </p>
          </div>
          <div class="flex items-center gap-3">
            <button
              type="button"
              class="px-4 py-2.5 rounded-full border border-indigo-500 border-opacity-40 text-purple-900 text-sm font-semibold bg-transparent disabled:opacity-50 disabled:cursor-not-allowed hover:bg-slate-50 transition-all"
              @click="clearReferences"
              :disabled="!referenceItems.length"
            >
              清除資料
            </button>
          </div>
        </header>

        <div class="bg-slate-50 p-5 rounded-2xl">
          <p class="font-semibold text-slate-900 mb-3">1. 補助與模板</p>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <label class="flex flex-col gap-2 text-sm text-slate-600">
              <span>補助主題 <span class="text-red-500">*</span></span>
              <select
                v-model="selectedGrantId"
                class="rounded-xl border border-slate-300 border-opacity-60 p-2.5 bg-white text-slate-900 disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                @change="handleGrantChange"
              >
                <option value="">請選擇</option>
                <option
                  v-for="grant in allConfigs"
                  :key="grant.id"
                  :value="grant.id"
                >
                  {{ grant.name }}
                </option>
              </select>
            </label>
            <label class="flex flex-col gap-2 text-sm text-slate-600">
              <span>模板 <span class="text-red-500">*</span></span>
              <select
                v-model="selectedTemplateId"
                class="rounded-xl border border-slate-300 border-opacity-60 p-2.5 bg-white text-slate-900 disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                :disabled="!selectedGrantId"
                @change="handleTemplateChange"
              >
                <option value="">
                  {{ selectedGrantId ? "請選擇模板" : "請先選擇補助" }}
                </option>
                <option
                  v-for="template in availableTemplates"
                  :key="template.id"
                  :value="template.id"
                >
                  {{ template.name }}
                </option>
              </select>
            </label>
          </div>
        </div>

        <div
          class="bg-white border border-slate-200 border-opacity-80 rounded-2xl p-5"
        >
          <p class="font-semibold text-slate-900 mb-3">2. 參考資料（可略過）</p>
          <div class="flex flex-col gap-3">
            <!-- 拖拽上傳區域 -->
            <div
              @dragover.prevent="isDraggingFiles = true"
              @dragleave.prevent="isDraggingFiles = false"
              @drop.prevent="handleFileDrop"
              class="border-2 border-dashed rounded-lg p-8 text-center transition-all"
              :class="
                isDraggingFiles
                  ? 'border-indigo-500 bg-indigo-50'
                  : 'border-slate-300 bg-slate-50 hover:border-indigo-400 hover:bg-indigo-50'
              "
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                class="h-12 w-12 mx-auto mb-3"
                :class="isDraggingFiles ? 'text-indigo-600' : 'text-slate-400'"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                />
              </svg>
              <p class="text-sm font-semibold text-slate-900 mb-1">
                拖拽檔案到此處
              </p>
              <p class="text-xs text-slate-600 mb-4">
                支持 Word (.docx) 和 Excel (.xlsx, .xls) 檔案
              </p>
              <div class="flex flex-wrap gap-3 justify-center">
                <button
                  type="button"
                  class="px-5 py-2.5 rounded-full bg-indigo-100 text-indigo-700 font-semibold text-sm disabled:opacity-60 disabled:cursor-not-allowed hover:bg-indigo-200 transition-all"
                  @click="triggerWordUpload"
                  :disabled="isImportingWord"
                >
                  {{ isImportingWord ? "解析中..." : "📄 匯入 Word (.docx)" }}
                </button>
                <button
                  type="button"
                  class="px-5 py-2.5 rounded-full bg-indigo-100 text-indigo-700 font-semibold text-sm disabled:opacity-60 disabled:cursor-not-allowed hover:bg-indigo-200 transition-all"
                  @click="triggerExcelUpload"
                  :disabled="isImportingExcel"
                >
                  {{
                    isImportingExcel
                      ? "解析中..."
                      : "📊 匯入 Excel 腳本 (.xlsx)"
                  }}
                </button>
                <a
                  :href="scriptTemplateUrl"
                  :download="scriptTemplateDownloadName"
                  class="px-5 py-2.5 rounded-full border border-indigo-500 border-opacity-40 text-indigo-700 font-semibold text-sm bg-white hover:bg-indigo-50 transition-all"
                >
                  📥 下載腳本模板
                </a>
              </div>
            </div>

            <input
              ref="wordInputRef"
              type="file"
              accept=".docx"
              class="hidden"
              @change="handleWordFileChange"
            />
            <input
              ref="excelInputRef"
              type="file"
              accept=".xlsx,.xls"
              class="hidden"
              @change="handleExcelFileChange"
            />
          </div>
          <ul v-if="referenceItems.length" class="mt-5 flex flex-col gap-3">
            <li
              v-for="item in referenceItems"
              :key="item.id"
              class="flex justify-between gap-4 p-4 border border-indigo-200 border-opacity-30 rounded-4xl bg-slate-50"
            >
              <div>
                <p class="font-semibold text-slate-900 text-center">
                  {{ item.title }}
                </p>
              </div>
              <button
                type="button"
                class="px-4 py-2.5 rounded-full border border-indigo-500 border-opacity-40 text-purple-900 text-sm font-semibold bg-transparent disabled:opacity-50 disabled:cursor-not-allowed hover:bg-slate-50 transition-all whitespace-nowrap"
                @click="removeReference(item.id)"
              >
                移除
              </button>
            </li>
          </ul>
        </div>

        <div class="flex flex-col gap-3 mt-2">
          <p class="text-xs text-slate-500">
            選擇完成後可直接前往下一階段，匯入資料可隨時略過。
          </p>
          <p
            v-if="!canProceedToChat"
            class="text-xs text-red-500 font-semibold"
          >
            請選擇補助主題和模板
          </p>
          <div class="flex gap-3 flex-wrap">
            <button
              type="button"
              class="px-6 py-2.5 rounded-full bg-gradient-to-r from-indigo-600 to-purple-500 text-white font-semibold disabled:opacity-50 disabled:cursor-not-allowed hover:from-indigo-500 hover:to-purple-400 transition-all"
              @click="handleProceedFromStageOne"
              :disabled="!canProceedToChat || isPreparingLinkStage"
            >
              {{ isPreparingLinkStage ? "準備中..." : "進入下一階段" }}
            </button>
          </div>
        </div>
      </section>

      <section
        v-else-if="currentStage === 2"
        class="bg-white rounded-3xl p-6 sm:p-8 shadow-lg flex flex-col gap-6"
      >
        <header class="space-y-2">
          <p class="text-xs uppercase tracking-widest text-indigo-600">
            第二階段 · 補充參考連結
          </p>
          <h2 class="text-2xl sm:text-3xl font-bold text-slate-900">
            使用鏈接補足未填欄位 （可略過）
          </h2>
          <p class="text-sm sm:text-base text-slate-600">
            系統僅會將分析結果填入目前仍為空白的欄位
          </p>
        </header>

        <div class="bg-slate-50 p-5 rounded-2xl border border-slate-100">
          <div
            class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between"
          >
            <div>
              <p class="text-sm font-semibold text-slate-900">剩餘待填欄位</p>
              <p v-if="analysisTargets.length" class="text-xs text-slate-500">
                尚有
                {{ analysisTargets.length }}
                個欄位仍為空白，可藉由參考連結補足。
              </p>
              <p v-else class="text-xs text-emerald-600">
                所有欄位皆已填寫完整，可直接前往對話階段。
              </p>
            </div>
            <span
              class="cursor-pointer text-xs px-3 py-1 rounded-full bg-indigo-100 text-indigo-700 font-semibold"
              :title="remainingFieldTooltip"
            >
              {{
                analysisTargets.length
                  ? `尚需補齊 ${analysisTargets.length} 項`
                  : "狀態良好"
              }}
            </span>
          </div>
        </div>

        <div class="space-y-4">
          <ReferenceLinker
            :links="referenceLinks"
            :available-fields="incompleteFields"
            @add="addReferenceLink"
            @remove="removeReferenceLink"
            @update="updateReferenceLink"
            @analyze="analyzeReferenceLink"
            @view-summary="openReferenceSummary"
          />
          <p class="text-xs text-slate-500">
            每個連結會在進入對話前自動分析，並僅填入仍為空白的欄位。你也可以自行點擊分析以即時預覽結果。
          </p>
        </div>

        <div class="flex flex-wrap gap-3 justify-end">
          <button
            type="button"
            class="px-4 py-2.5 rounded-full border border-slate-300 text-slate-700 text-sm font-semibold hover:bg-slate-50"
            @click="restartFlow"
            :disabled="isPreparingForChat"
          >
            重新開始
          </button>
          <button
            type="button"
            class="px-6 py-2.5 rounded-full bg-gradient-to-r from-indigo-600 to-purple-500 text-white font-semibold disabled:opacity-50 disabled:cursor-not-allowed hover:from-indigo-500 hover:to-purple-400 transition-all"
            @click="enterChatStage"
            :disabled="isPreparingForChat"
          >
            {{ isPreparingForChat ? "分析中..." : "完成並進入對話" }}
          </button>
        </div>
      </section>

      <section
        v-else-if="currentStage === 3"
        class="h-screen flex flex-col gap-0"
      >
        <Chatbox
          :key="chatSessionKey"
          class="flex-1"
          :sections="currentSections"
          :reference-summaries="referenceSummaries"
          :candidate-plan="candidatePlan"
          :final-plan="finalPlanContent"
          :is-generating="isLoading"
          :grant-id="selectedGrantId"
          :template-id="selectedTemplateId"
          :grant-name="selectedGrantName"
          :template-name="selectedTemplateName"
          :use-model-type="useModelType"
          :prefilled-answers="prefilledChatAnswers"
          project-id=""
          @generatePlan="handleGeneratePlan"
          @finalizeCandidates="onCandidateConfirm"
          @requestExport="handleExportWord"
          @toggleModel="toggleModel"
          @backToStageOne="restartFlow"
        />
      </section>
    </div>
  </div>

  <div
    v-if="isLinkSummaryModalVisible"
    class="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-30"
    @click.self="isLinkSummaryModalVisible = false"
  >
    <div class="bg-white rounded-2xl shadow-xl max-w-lg w-full p-6 space-y-4">
      <div>
        <p class="text-sm text-slate-500">來源連結</p>
        <p class="text-base font-semibold text-slate-900 truncate">
          {{ linkSummaryTitle }}
        </p>
      </div>
      <pre
        class="max-h-[60vh] overflow-y-auto text-sm text-slate-700 whitespace-pre-wrap"
        >{{ linkSummaryContent }}</pre
      >
      <div class="flex justify-end">
        <button
          type="button"
          class="px-4 py-2 rounded-full bg-slate-200 text-slate-800 text-sm font-semibold"
          @click="isLinkSummaryModalVisible = false"
        >
          關閉
        </button>
      </div>
    </div>
  </div>
</template>
<script setup>
import { computed, onMounted, ref } from "vue";
import Chatbox from "~/components/Chatbox.vue";
import ReferenceLinker from "~/components/ReferenceLinker.vue";
import { usePlanGenerator } from "~/composables/usePlanGenerator";
import { useLoading } from "~/composables/useLoading";
import { useNotifications } from "~/composables/useNotifications";
import { useCurrentUser } from "~/composables/useCurrentUser";
import {
  extractTextFromWord,
  callAutoFillApi,
  buildSectionSchema,
  processAutoFillResults,
} from "~/utils/wordImport";
import {
  applyExcelRows,
  buildExcelReplyTargetMap,
  extractExcelRows,
} from "~/utils/excelImport";
import {
  buildDynamicSections,
  createEmptyDynamicValues,
  makeCompositeKey,
  mergeIntoEmptyValues,
} from "~/utils/dynamicSchema";
import { exportPlanToWord } from "~/utils/exportToWord";

definePageMeta({
  middleware: "auth",
});

// SEO 配置
useHead({
  title: "AI 計畫書生成器 - 專業提案一鍵生成",
  meta: [
    {
      name: "description",
      content:
        "使用 AI 技術快速生成專業計畫書。支持多種主題和模板，提高提案效率。",
    },
    {
      name: "keywords",
      content: "計畫書,AI 生成,提案,企劃書,自動化",
    },
    {
      property: "og:title",
      content: "AI 計畫書生成器 - 專業提案一鍵生成",
    },
    {
      property: "og:description",
      content:
        "使用 AI 技術快速生成專業計畫書。支持多種主題和模板，提高提案效率。",
    },
    {
      property: "og:type",
      content: "website",
    },
  ],
});

const { isLoading, show: showLoading, hide: hideLoading } = useLoading();
const {
  success,
  error: errorNotification,
  warning: notifyWarning,
} = useNotifications();
const config = useRuntimeConfig();
const API_BASE_URL = `${config.public.apiBaseUrl}/api`;

const useModelType = ref("external");

const {
  selectedGrantId,
  selectedTemplateId,
  planContent: finalPlanContent,
  currentSections,
  allConfigs,
  onSelectionChange,
  dynamicFieldValues,
} = usePlanGenerator();

const candidatePlan = ref({});
const referenceItems = ref([]);
const wordInputRef = ref(null);
const excelInputRef = ref(null);
const isImportingWord = ref(false);
const isImportingExcel = ref(false);
const isDraggingFiles = ref(false);
const currentStage = ref(1);
const chatSessionKey = ref(0);
const prefillMainIdea = ref("");
const scriptTemplateUrl = "/腳本格式(通用).xlsx";
const scriptTemplateDownloadName = "腳本格式(通用).xlsx";
const referenceLinks = ref([]);
const wordAutofillQueue = ref([]);
const isPreparingLinkStage = ref(false);
const isPreparingForChat = ref(false);
const isLinkSummaryModalVisible = ref(false);
const linkSummaryContent = ref("");
const linkSummaryTitle = ref("");
const lastGenerationPrompt = ref("");
const { userId: currentUserId, refreshUser } = useCurrentUser();
onMounted(() => {
  refreshUser();
});

const dynamicSections = computed(() =>
  buildDynamicSections(dynamicFieldValues.value)
);

const excelReplyTargetMap = computed(() =>
  buildExcelReplyTargetMap(dynamicSections.value)
);

async function getUserIdOrNotify() {
  const userId = currentUserId.value || (await refreshUser());
  if (!userId) {
    errorNotification("無法取得使用者資訊，請重新登入後再試。");
  }
  return userId;
}

const prefilledChatAnswers = computed(() => {
  const answers = {};
  const valueEntries = dynamicFieldValues.value || {};
  Object.entries(valueEntries).forEach(([compositeKey, value]) => {
    if (!value || !String(value).trim()) {
      return;
    }
    const [sectionId, propertyKey, subFieldKey] = compositeKey.split("::");
    if (!sectionId || !propertyKey || subFieldKey !== "reply") {
      return;
    }
    answers[`${sectionId}::${propertyKey}`] = String(value).trim();
  });
  if (prefillMainIdea.value && prefillMainIdea.value.trim()) {
    answers["main-idea"] = prefillMainIdea.value.trim();
  }
  return answers;
});

const incompleteFields = computed(() => {
  const sections = dynamicSections.value || [];
  return sections.flatMap((section) =>
    section.fields.flatMap((field) =>
      field.subFields
        .filter((sub) => !sub.value || !String(sub.value).trim())
        .map((sub) => ({
          section_id: section.sectionId,
          property_key: field.propertyKey,
          sub_field_key: sub.key,
          label: `${section.sectionName} · ${field.title}${
            sub.shortLabel ? ` (${sub.shortLabel})` : ""
          }`,
        }))
    )
  );
});

const analysisTargets = computed(() =>
  incompleteFields.value.map(({ section_id, property_key, sub_field_key }) => ({
    section_id,
    property_key,
    sub_field_key,
  }))
);

const remainingFieldTooltip = computed(() =>
  incompleteFields.value.map((field) => field.label).join("\n")
);

const selectedGrant = computed(
  () =>
    allConfigs.value.find((grant) => grant.id === selectedGrantId.value) || null
);

const availableTemplates = computed(() => selectedGrant.value?.templates || []);

const selectedGrantName = computed(() => selectedGrant.value?.name || "");

const selectedTemplateName = computed(() => {
  const target = availableTemplates.value.find(
    (tpl) => tpl.id === selectedTemplateId.value
  );
  return target?.name || "";
});

const canProceedToChat = computed(() =>
  Boolean(selectedGrantId.value && selectedTemplateId.value)
);

const referenceSummaries = computed(() =>
  referenceItems.value.map(
    (item, idx) => `#${idx + 1} ${item.title}\n${item.preview}`
  )
);

function onCandidateConfirm({ selected, rejected }) {
  const newPlanContent = {};
  for (const [sectionId, candidate] of Object.entries(selected)) {
    if (candidate && candidate.content) {
      newPlanContent[sectionId] = { content: candidate.content };
    } else {
      newPlanContent[sectionId] = { error: candidate?.error || "No content" };
    }
  }
  finalPlanContent.value = newPlanContent;
  success("已選擇方案並填充到結果中！");
  savePreferenceData(selected, rejected, lastGenerationPrompt.value);
}

async function savePreferenceData(
  selectedData,
  rejectedData,
  finalPrompt = ""
) {
  try {
    const entriesToSave = currentSections.value
      .map((section) => {
        const chosen = selectedData[section.id];
        const rejected = rejectedData[section.id];

        if (chosen && chosen.content) {
          return {
            source_type: "external_direct",
            grant_id: selectedGrantId.value,
            template_id: selectedTemplateId.value,
            section_id: section.id,
            prompt: finalPrompt || "conversation_mode",
            final_answer: chosen.content,
            rejected_answer: rejected?.content || null,
          };
        }
        return null;
      })
      .filter(Boolean);

    if (entriesToSave.length > 0) {
      // 使用 fetch 發送到 /api/datasets，不阻塞用戶 UI
      fetch(`${API_BASE_URL}/datasets`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ entries: entriesToSave }),
      }).then((response) => {
        if (response.status !== 202) {
          console.error("後台保存偏好數據失敗。");
        }
      });
    }
  } catch (e) {
    console.error("準備保存偏好數據時出錯:", e);
  }
}

// --- 页面独有的方法 ---
function handleGrantChange() {
  selectedTemplateId.value = "";
  syncSelectionState();
}

function handleTemplateChange() {
  syncSelectionState();
}

function syncSelectionState() {
  onSelectionChange({
    grantId: selectedGrantId.value,
    templateId: selectedTemplateId.value,
  });
  resetReferenceCollections();
  prefillMainIdea.value = "";
  resetChatSession();
  currentStage.value = 1;
}

async function handleProceedFromStageOne() {
  if (!selectedGrantId.value || !selectedTemplateId.value) {
    errorNotification("請先完成補助與模板的選擇");
    return;
  }

  if (isPreparingLinkStage.value) {
    return;
  }

  isPreparingLinkStage.value = true;
  try {
    await runWordAutofillQueue();
    currentStage.value = 2;
  } catch (error) {
    console.error("Failed to prepare Link Stage", error);
    errorNotification(`Word 自動填寫失敗：${error?.message || "未知錯誤"}`);
  } finally {
    isPreparingLinkStage.value = false;
  }
}

async function enterChatStage() {
  if (!canProceedToChat.value || isPreparingForChat.value) {
    return;
  }

  // 檢查是否所有參考連結都已搜索
  const unsearchedLinks = referenceLinks.value.filter(
    (link) => link.url && link.status === "pending"
  );
  if (unsearchedLinks.length > 0) {
    errorNotification(
      `還有 ${unsearchedLinks.length} 個參考連結未檢索，請先完成搜索。`
    );
    return;
  }

  isPreparingForChat.value = true;
  try {
    await runWordAutofillQueue();
    await runReferenceAutofillQueue();
    resetChatSession();
    currentStage.value = 3;
  } catch (error) {
    console.error("Failed to prepare Chat Stage", error);
    errorNotification(`資料準備失敗：${error?.message || "未知錯誤"}`);
  } finally {
    isPreparingForChat.value = false;
  }
}

function restartFlow() {
  syncSelectionState();
}

function resetChatSession() {
  candidatePlan.value = {};
  finalPlanContent.value = {};
  chatSessionKey.value += 1;
}

async function handleGeneratePlan(payload) {
  if (!payload?.prompt || !selectedTemplateId.value || !selectedGrantId.value) {
    errorNotification("請先完成補助與模板挑選，並輸入至少一則對話訊息。");
    return;
  }
  showLoading("正在生成計劃書...", true);
  finalPlanContent.value = {};
  candidatePlan.value = {};
  lastGenerationPrompt.value = payload.prompt;

  try {
    const sectionsToGenerate = currentSections.value.map((s) => ({
      section_id: s.id,
    }));
    const {
      data: { session },
    } = await supabase.auth.getSession();

    if (!session?.access_token) {
      hideLoading();
      errorNotification("請先登入");
      return;
    }

    const response = await fetch(`${API_BASE_URL}/generate_plan`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${session.access_token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        grant: selectedGrantId.value,
        template: selectedTemplateId.value,
        user_input: payload.prompt,
        num_candidates: 2,
        is_external: useModelType.value === "external",
      }),
    });

    if (!response.ok) {
      const errorDetail = await response.text();
      throw new Error(`伺服器錯誤 (${response.status}): ${errorDetail}`);
    }

    const rawData = await response.json();

    const processedCandidates = {};
    for (const sectionId in rawData) {
      const candidates = rawData[sectionId]; // candidates 现在是一个数组
      processedCandidates[sectionId] = candidates.map((candidate) => ({
        content: candidate.raw_json_content,
        error: candidate.error || null,
      }));
    }

    candidatePlan.value = processedCandidates;
    success("計劃書草稿已生成！");
  } catch (error) {
    console.error("生成計劃書時發生錯誤:", error);
    errorNotification(`生成失敗: ${error.message}`);
  } finally {
    hideLoading();
  }
}

function triggerWordUpload() {
  if (isImportingWord.value) return;
  wordInputRef.value?.click();
}

function triggerExcelUpload() {
  if (isImportingExcel.value) return;
  excelInputRef.value?.click();
}

function handleFileDrop(event) {
  isDraggingFiles.value = false;
  const files = event.dataTransfer?.files;
  if (!files || files.length === 0) return;

  for (const file of files) {
    if (file.name.endsWith(".docx")) {
      const syntheticEvent = { target: { files: [file], value: "" } };
      handleWordFileChange(syntheticEvent);
    } else if (file.name.endsWith(".xlsx") || file.name.endsWith(".xls")) {
      const syntheticEvent = { target: { files: [file], value: "" } };
      handleExcelFileChange(syntheticEvent);
    }
  }
}

async function handleWordFileChange(event) {
  const file = event.target.files?.[0];
  event.target.value = "";
  if (!file) return;

  if (!selectedTemplateId.value) {
    notifyWarning("請先選擇補助與模板，才能匯入 Word 檔案");
    return;
  }

  isImportingWord.value = true;
  try {
    const rawText = await extractTextFromWord(file);
    const normalized = (rawText || "").replace(/\s+/g, " ").trim();
    if (!normalized) {
      notifyWarning("無法從 Word 檔讀取內容，請確認檔案是否為純文字。");
      return;
    }
    pushReferenceItem({
      title: file.name,
      preview: normalized.slice(0, 800),
    });
    wordAutofillQueue.value = [
      ...wordAutofillQueue.value,
      {
        id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
        title: file.name,
        documentText: rawText,
      },
    ];
    success("已將 Word 檔轉換為參考摘要");
  } catch (error) {
    console.error("word import failed", error);
    errorNotification(`匯入失敗：${error.message}`);
  } finally {
    isImportingWord.value = false;
  }
}

async function handleExcelFileChange(event) {
  const file = event.target.files?.[0];
  event.target.value = "";
  if (!file) return;

  if (!selectedTemplateId.value) {
    notifyWarning("請先選擇補助與模板，才能套用 Excel 腳本");
    return;
  }

  isImportingExcel.value = true;
  try {
    // 清空動態欄位值
    dynamicFieldValues.value = createEmptyDynamicValues();

    // 刪除之前的 Excel 檔案（只保留一個）
    referenceItems.value = referenceItems.value.filter(
      (item) => !item.title.endsWith(".xlsx") && !item.title.endsWith(".xls")
    );

    const buffer = await file.arrayBuffer();
    const rows = extractExcelRows(buffer);
    if (!rows.length) {
      notifyWarning("此 Excel 未讀到可用資料");
      return;
    }
    const preview = rows
      .slice(0, 6)
      .map((row, idx) => {
        const pairs = Object.entries(row)
          .filter(([, value]) => value && `${value}`.trim() !== "")
          .map(([key, value]) => `${key}: ${value}`)
          .join(" | ");
        return `#${idx + 1} ${pairs}`;
      })
      .join("\n");
    pushReferenceItem({
      title: file.name,
      preview: preview || "未偵測到欄位內容",
    });
    const nextValues = mergeIntoEmptyValues(dynamicFieldValues.value);
    const result = applyExcelRows({
      rows,
      dynamicSections: dynamicSections.value,
      replyTargetMap: excelReplyTargetMap.value,
      onFill: (sectionId, propertyKey, subFieldKey, value) => {
        const compositeKey = makeCompositeKey(
          sectionId,
          propertyKey,
          subFieldKey
        );
        nextValues[compositeKey] = value;
      },
    });

    dynamicFieldValues.value = nextValues;
    if (result.summaryText) {
      prefillMainIdea.value = result.summaryText;
    }

    const messageParts = [];
    if (result.summaryText) {
      messageParts.push("已帶入摘要內容");
    }
    if (result.appliedCount > 0) {
      messageParts.push(`填入 ${result.appliedCount} 個欄位`);
    }
    if (result.skippedCount > 0) {
      messageParts.push(`略過 ${result.skippedCount} 筆未匹配欄位`);
    }

    if (messageParts.length > 0) {
      success(`Excel 匯入完成：${messageParts.join("、")}`);
    } else if (result.appliedCount === 0) {
      // 沒有匹配到任何欄位
      errorNotification("此 Excel 未匹配到任何欄位，請按照腳本模板重新填寫");
    } else {
      success("已將 Excel 內容轉為文字摘要");
    }
  } catch (error) {
    console.error("excel import failed", error);
    errorNotification(`匯入失敗：${error.message}`);
  } finally {
    isImportingExcel.value = false;
  }
}

function pushReferenceItem({ title, preview }) {
  referenceItems.value = [
    ...referenceItems.value,
    {
      id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
      title,
      preview,
    },
  ];
}

function resetReferenceCollections() {
  referenceItems.value = [];
  referenceLinks.value = [];
  wordAutofillQueue.value = [];
  linkSummaryContent.value = "";
  linkSummaryTitle.value = "";
  isLinkSummaryModalVisible.value = false;
}

function removeReference(id) {
  const item = referenceItems.value.find((item) => item.id === id);
  referenceItems.value = referenceItems.value.filter((item) => item.id !== id);

  // 移除 Excel 檔案時清空動態欄位值
  if (item && (item.title.endsWith(".xlsx") || item.title.endsWith(".xls"))) {
    dynamicFieldValues.value = createEmptyDynamicValues();
    prefillMainIdea.value = "";
  }

  if (item && item.title.endsWith(".docx")) {
    wordAutofillQueue.value = wordAutofillQueue.value.filter(
      (doc) => doc.title !== item.title
    );
  }
}

function clearReferences() {
  resetReferenceCollections();
  prefillMainIdea.value = "";
  dynamicFieldValues.value = createEmptyDynamicValues();
}

function addReferenceLink() {
  referenceLinks.value = [
    ...referenceLinks.value,
    { url: "", status: "pending", summary: "" },
  ];
}

function removeReferenceLink(index) {
  referenceLinks.value = referenceLinks.value.filter((_, i) => i !== index);
}

function updateReferenceLink({ index, field, value }) {
  const nextLinks = [...referenceLinks.value];
  if (!nextLinks[index]) {
    return;
  }
  nextLinks[index] = {
    ...nextLinks[index],
    [field]: value,
  };
  if (field === "url") {
    nextLinks[index].status = "pending";
    nextLinks[index].summary = "";
  }
  referenceLinks.value = nextLinks;
}

function openReferenceSummary(index) {
  const target = referenceLinks.value[index];
  if (!target) {
    return;
  }
  linkSummaryTitle.value = target.url || `參考連結 #${index + 1}`;
  linkSummaryContent.value = target.summary || "暫無摘要";
  isLinkSummaryModalVisible.value = true;
}

async function analyzeReferenceLink(index, options = {}) {
  const link = referenceLinks.value[index];
  if (!link || !link.url) {
    return;
  }

  const loadingLinks = [...referenceLinks.value];
  loadingLinks[index] = {
    ...link,
    status: "loading",
  };
  referenceLinks.value = loadingLinks;

  try {
    const selectedFieldLabels =
      link.selectedFields && link.selectedFields.length > 0
        ? link.selectedFields
        : null; // null means random selection (default behavior)

    const response = await fetch(`${API_BASE_URL}/scrape_and_analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        url: link.url,
        context_targets: selectedFieldLabels
          ? analysisTargets.value.filter((target) =>
              selectedFieldLabels.some((label) =>
                label.includes(target.property_key)
              )
            )
          : analysisTargets.value,
        max_items: selectedFieldLabels ? selectedFieldLabels.length : 4, // 複選時使用選擇欄位數，否則限制為4
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || "分析失敗");
    }

    const result = await response.json();
    const summaryText =
      typeof result.summary === "string" ? result.summary.trim() : "";
    const autoFillItems = Array.isArray(result.auto_fill)
      ? result.auto_fill
      : [];
    const appliedEntries = applyAutoFillEntries(autoFillItems);

    const summaryLines = [];
    if (summaryText) {
      summaryLines.push(summaryText);
    }
    if (appliedEntries.length > 0) {
      if (summaryLines.length) {
        summaryLines.push("");
      }
      summaryLines.push("自動填寫欄位：");
      appliedEntries.forEach((entry) => {
        const label = entry.label || entry.compositeKey;
        summaryLines.push(`- ${label}: ${entry.content}`);
      });
    }

    const completedLinks = [...referenceLinks.value];
    completedLinks[index] = {
      ...completedLinks[index],
      status: "completed",
      summary: summaryLines.join("\n").trim() || "此連結未產生可用資訊。",
      selectedFields: undefined, // 清空selectedFields
    };
    referenceLinks.value = completedLinks;
  } catch (error) {
    console.error(`Error analyzing link ${link.url}`, error);
    const erroredLinks = [...referenceLinks.value];
    erroredLinks[index] = {
      ...erroredLinks[index],
      status: "error",
      summary: `分析失敗：${error.message}`,
    };
    referenceLinks.value = erroredLinks;
    if (!options.silent) {
      errorNotification(`連結分析失敗：請確認網址正確且可存取`);
    }
  }
}

function applyAutoFillEntries(autoFillItems = []) {
  if (!Array.isArray(autoFillItems) || autoFillItems.length === 0) {
    return [];
  }

  const workingValues = mergeIntoEmptyValues(dynamicFieldValues.value);
  const applied = [];

  autoFillItems.forEach((item) => {
    const compositeKey = (item.composite_key || item.compositeKey || "").trim();
    if (!compositeKey) {
      return;
    }
    const [sectionId, propertyKey, subFieldKey] = compositeKey.split("::");
    if (!sectionId || !propertyKey || !subFieldKey) {
      return;
    }
    const content = (item.content || "").trim();
    if (!content) {
      return;
    }
    const currentValue = workingValues[compositeKey] || "";
    if (currentValue && currentValue.trim()) {
      return;
    }
    workingValues[compositeKey] = content;
    applied.push({ compositeKey, label: item.label || "", content });
  });

  dynamicFieldValues.value = workingValues;
  return applied;
}

function applyWordAutoFillResults(filledContent) {
  if (!filledContent || typeof filledContent !== "object") {
    return;
  }

  const workingValues = mergeIntoEmptyValues(dynamicFieldValues.value);
  const updater = (sectionId, propertyKey, subFieldKey, value) => {
    const compositeKey = makeCompositeKey(sectionId, propertyKey, subFieldKey);
    const currentValue = workingValues[compositeKey];
    if (currentValue && currentValue.trim()) {
      return;
    }
    workingValues[compositeKey] = value;
  };

  processAutoFillResults(
    filledContent,
    dynamicSections.value,
    updater,
    () => {}
  );

  dynamicFieldValues.value = workingValues;

  const mainIdeaContent =
    filledContent?.main_idea?.content?.project_name_and_summary?.trim();
  if (mainIdeaContent && !prefillMainIdea.value.trim()) {
    prefillMainIdea.value = mainIdeaContent;
  }
}

async function runWordAutofillQueue() {
  const queue = wordAutofillQueue.value.filter(
    (doc) => doc.documentText && doc.documentText.trim()
  );

  if (!queue.length) {
    return;
  }

  if (!dynamicSections.value.length) {
    notifyWarning("目前尚未載入可填寫的章節，已略過 Word 自動填寫。");
    wordAutofillQueue.value = [];
    return;
  }

  wordAutofillQueue.value = [];

  try {
    // 合併所有 Word 文字
    const combinedText = queue
      .map((doc) => doc.documentText)
      .join("\n\n---\n\n");
    const userId = await getUserIdOrNotify();
    if (!userId) {
      return;
    }

    const payload = {
      document_text: combinedText,
      sections: dynamicSections.value.map((section) => ({
        section_id: section.sectionId,
        section_name: section.sectionName,
        json_schema: buildSectionSchema(section),
      })),
      user_id: userId,
    };

    const filledContent = await callAutoFillApi(payload, API_BASE_URL);
    applyWordAutoFillResults(filledContent);

    const docTitles = queue.map((doc) => doc.title).join("、");
    success(`${docTitles} 已完成欄位自動填寫`);
  } catch (error) {
    console.error("Word autofill failed", error);
    errorNotification(`Word 自動填寫失敗：${error?.message || "未知錯誤"}`);
  }
}

async function runReferenceAutofillQueue() {
  if (!referenceLinks.value.length) {
    return;
  }

  for (let i = 0; i < referenceLinks.value.length; i += 1) {
    const link = referenceLinks.value[i];
    if (!link.url || link.status === "completed") {
      continue;
    }
    await analyzeReferenceLink(i);
  }
}

function handleExportWord() {
  const hasPlan = Object.keys(finalPlanContent.value || {}).length > 0;
  if (!hasPlan) {
    notifyWarning("尚未有可匯出的內容");
    return;
  }
  return exportPlanToWord(
    currentSections.value,
    finalPlanContent.value,
    selectedGrantId.value,
    selectedTemplateId.value
  );
}

function toggleModel() {
  useModelType.value =
    useModelType.value === "internal" ? "external" : "internal";
}
</script>
