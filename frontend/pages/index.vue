<template>
  <ClientOnly>
    <div class="min-h-screen bg-gray-50 px-4 py-6 md:px-8">
      <div class="mx-auto max-w-6xl space-y-6">
        <p
          class="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-gray-400"
        >
          <NuxtLink to="/" class="hover:text-gray-600">首頁</NuxtLink>
          <span class="text-gray-300">></span>
          <span class="text-gray-600">計劃書生成精靈</span>
        </p>
        <!-- Stage 1: 選擇計畫類型 -->
        <section
          v-if="currentStage === 1"
          class="rounded-[32px] px-6 py-8 lg:px-10"
        >
          <div class="text-center">
            <p
              class="text-3xl font-semibold uppercase tracking-[0.35em] text-rose-500"
            >
              請選擇目標補助計畫
            </p>
            <p class="mt-2 text-sm text-[#5f6c96]">
              系統會依照類型載入對應的模型與模板組態
            </p>
          </div>

          <div class="mt-8 grid gap-5 md:grid-cols-2 xl:grid-cols-3">
            <button
              v-for="plan in planTypes"
              :key="plan.id"
              class="flex h-full flex-col rounded-xl border border-[#eef0f7] bg-white p-6 text-left shadow-sm transition"
              :class="
                selectedPlanType?.id === plan.id
                  ? 'border-2 border-rose-400 shadow-lg shadow-rose-100'
                  : 'hover:-translate-y-0.5 hover:border-[#d7e0ff]'
              "
              @click="handlePlanClick(plan)"
            >
              <span
                class="inline-flex h-12 w-12 items-center justify-center rounded-2xl"
                :class="plan.iconBg"
              >
                <Icon
                  :name="plan.icon"
                  class="h-6 w-6"
                  :style="{ color: plan.iconColor }"
                />
              </span>
              <p
                class="mt-3 text-[11px] font-semibold uppercase tracking-[0.35em] text-[#8a94c1]"
              >
                {{ plan.category }}
              </p>
              <h3 class="mt-1 text-xl font-semibold text-[#111b3f]">
                {{ plan.title }}
              </h3>
              <p class="mt-3 text-sm font-semibold text-[#7d86ad]">
                {{ plan.subtitle }}
              </p>
              <p class="mt-1 text-xs text-[#8f98be]">
                {{ plan.description }}
              </p>
              <div
                class="mt-4 flex flex-wrap gap-2 text-[11px] font-semibold text-[#97a0c7]"
              >
                <span
                  v-for="tag in plan.tags"
                  :key="tag"
                  class="rounded-full border border-[#e6e9fb] bg-white px-3 py-1"
                >
                  {{ tag }}
                </span>
              </div>
            </button>
          </div>

          <div class="mt-8 flex flex-wrap items-center justify-center gap-3">
            <button
              class="rounded-2xl border border-[#d9def5] px-6 py-2 text-sm font-semibold text-[#6974a8] transition hover:border-[#c5cced]"
              type="button"
              @click="router.push('/')"
            >
              取消
            </button>
            <button
              class="rounded-2xl bg-rose-500 px-6 py-2 text-sm font-semibold text-white shadow-lg shadow-rose-200 transition hover:-translate-y-0.5 hover:bg-rose-600"
              type="button"
              :disabled="!canConfirmPlanType"
              :class="{ 'opacity-60 cursor-not-allowed': !canConfirmPlanType }"
              @click="handlePlanTypeConfirm"
            >
              下一步
            </button>
          </div>
        </section>

        <!-- Stage 2: 填寫簡報資訊 -->
        <section
          v-else-if="currentStage === 2"
          class="rounded-3xl bg-white p-6 shadow-lg lg:p-8"
        >
          <header class="flex flex-wrap items-start justify-between gap-4">
            <div class="space-y-2">
              <h2 class="text-2xl font-semibold text-slate-900">
                為 {{ selectedPlanType?.title || "選定計畫" }} 建立專屬企劃
              </h2>
              <p class="text-sm text-slate-500">
                這些資訊會作為進入 Chatbox 前的基礎情境，AI 會優先引用這些內容。
              </p>
            </div>
            <button
              class="rounded-full border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-500"
              type="button"
              @click="backToStage(1)"
            >
              重新選擇類型
            </button>
          </header>

          <!-- <div class="mt-6 grid gap-4 md:grid-cols-2">
            <button
              v-for="mode in modeOptions"
              :key="mode.id"
              class="flex h-full flex-col rounded-3xl border p-5 text-left transition"
              :class="
                selectedMode === mode.id
                  ? 'border-rose-400 bg-rose-50 shadow-md'
                  : 'border-slate-100 bg-slate-50 shadow-sm hover:border-rose-200 hover:bg-white'
              "
              @click="selectedMode = mode.id"
            >
              <p
                class="text-xs font-semibold uppercase tracking-widest text-slate-400"
              >
                {{ mode.badge }}
              </p>
              <h3 class="mt-2 text-xl font-semibold text-slate-900">
                {{ mode.title }}
              </h3>
              <p class="mt-2 text-sm text-slate-500">
                {{ mode.description }}
              </p>
            </button>
          </div> -->

          <div class="mt-6 space-y-4">
            <label class="block space-y-2">
              <span class="text-sm font-semibold text-slate-700"
                >計畫名稱 <span class="text-red-500">*</span></span
              >
              <input
                v-model="planName"
                type="text"
                class="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 outline-none focus:border-rose-400 focus:bg-white"
                placeholder="例：2025 智慧服務輸出 SIIR 計畫"
              />
            </label>
            <label class="block space-y-2">
              <span class="text-sm font-semibold text-slate-700"
                >計畫摘要 <span class="text-red-500">*</span></span
              >
              <textarea
                v-model="planSummary"
                rows="4"
                class="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 outline-none focus:border-rose-400 focus:bg-white"
                placeholder="用 2-3 句描述計畫目標、受惠對象與成果。"
              ></textarea>
            </label>
            <label class="block space-y-2">
              <span class="text-sm font-semibold text-slate-700"
                >專屬背景資料</span
              >
            </label>
            <div
              class="space-y-4 rounded-2xl border border-slate-200 bg-slate-50 p-5"
            >
              <div class="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p class="text-xs text-slate-500">
                    支援 Word (.docx) 與 PDF 檔案，系統會將文字內容轉為摘要供 AI
                    優先引用。
                  </p>
                </div>
                <button
                  v-if="backgroundFiles.length"
                  type="button"
                  class="rounded-full border border-slate-300 px-4 py-2 text-xs font-semibold text-slate-500 hover:border-rose-200 hover:text-rose-500"
                  @click="clearBackgroundAttachments"
                >
                  清空附件
                </button>
              </div>
              <div
                class="rounded-2xl border-2 border-dashed border-slate-300 bg-white/80 p-6 text-center transition"
                :class="
                  isDraggingBackground
                    ? 'border-rose-400 bg-white shadow-inner'
                    : 'hover:border-rose-300'
                "
                @dragover.prevent="isDraggingBackground = true"
                @dragleave.prevent="isDraggingBackground = false"
                @drop.prevent="handleBackgroundDrop"
              >
                <div
                  class="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-rose-50 text-rose-500"
                >
                  <Icon name="ph:paperclip-light" class="h-6 w-6" />
                </div>
                <p class="mt-3 text-sm font-semibold text-slate-800">
                  {{
                    isProcessingBackground
                      ? "正在解析附件..."
                      : "拖曳 Word / PDF 檔案到此處"
                  }}
                </p>
                <p class="mt-1 text-xs text-slate-500">
                  或
                  <button
                    type="button"
                    class="font-semibold text-rose-500 underline decoration-rose-200 decoration-2 underline-offset-4"
                    @click="triggerBackgroundUpload"
                    :disabled="isProcessingBackground"
                  >
                    點此選擇檔案
                  </button>
                </p>
                <p
                  class="mt-1 text-[11px] uppercase tracking-[0.3em] text-slate-400"
                >
                  目前已加入 {{ backgroundFiles.length }} 份附件
                </p>
              </div>
              <input
                ref="backgroundFileInputRef"
                type="file"
                accept=".docx,.pdf"
                class="hidden"
                multiple
                @change="handleBackgroundFileChange"
              />
              <ul v-if="backgroundFiles.length" class="space-y-3">
                <li
                  v-for="file in backgroundFiles"
                  :key="file.id"
                  class="flex flex-col gap-3 rounded-2xl border border-slate-200 bg-white p-4 sm:flex-row sm:items-center sm:justify-between"
                >
                  <div class="flex items-start gap-3">
                    <span
                      class="mt-1 inline-flex h-10 w-10 items-center justify-center rounded-xl text-sm font-semibold"
                      :class="
                        file.type === 'word'
                          ? 'bg-rose-50 text-rose-500'
                          : 'bg-slate-100 text-slate-600'
                      "
                    >
                      {{ file.type === "word" ? "DOC" : "PDF" }}
                    </span>
                    <div>
                      <p class="text-sm font-semibold text-slate-800">
                        {{ file.name }}
                      </p>
                      <p class="mt-1 text-xs text-slate-500 sm:max-w-md">
                        {{ file.snippet || "未偵測到可用文字內容" }}
                      </p>
                    </div>
                  </div>
                  <button
                    type="button"
                    class="self-start rounded-full border border-slate-200 px-4 py-1.5 text-xs font-semibold text-slate-500 hover:border-rose-200 hover:text-rose-500"
                    @click="removeBackgroundAttachment(file.id)"
                  >
                    移除
                  </button>
                </li>
              </ul>
            </div>
          </div>

          <div class="mt-6 flex flex-wrap items-center justify-between gap-3">
            <p class="text-sm text-slate-400">
              將以 {{ resolvedTemplateName || "預設模板" }} 啟動 Chatbox。
            </p>
            <div class="flex gap-3">
              <button
                class="rounded-2xl border border-slate-200 px-5 py-2 text-sm font-semibold text-slate-500"
                type="button"
                @click="backToStage(1)"
              >
                上一步
              </button>
              <button
                class="rounded-2xl bg-rose-500 px-6 py-2 text-sm font-semibold text-white shadow-lg shadow-rose-200 transition hover:-translate-y-0.5 hover:bg-rose-600"
                type="button"
                :disabled="
                  !canEnterChat || isProcessingBackground || isCreatingProject
                "
                :class="{
                  'opacity-60 cursor-not-allowed':
                    !canEnterChat ||
                    isProcessingBackground ||
                    isCreatingProject,
                }"
                @click="enterChatStage"
              >
                {{
                  isProcessingBackground
                    ? "解析附件中..."
                    : isCreatingProject
                    ? "建立工作區..."
                    : "進入工作區"
                }}
              </button>
            </div>
          </div>
        </section>
      </div>
    </div>
  </ClientOnly>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { usePlanGenerator } from "~/composables/usePlanGenerator";
import { useNotifications } from "~/composables/useNotifications";
import { useCurrentUser } from "~/composables/useCurrentUser";
import { useFileExtractor } from "~/composables/useFileExtractor";

useHead({
  title: "計劃書生成精靈 - TGSA 企劃引擎",
  meta: [
    {
      name: "description",
      content:
        "AI 驅動的計劃書生成工具，支援 SIIR、IMDP、CITD 等多種補助計畫類型，一鍵生成專業計畫書草稿。",
    },
    {
      name: "keywords",
      content: "計劃書生成, AI 企劃, 政府補助, SIIR, IMDP, CITD, 智能寫作",
    },
    {
      property: "og:title",
      content: "計劃書生成精靈 - TGSA 企劃引擎",
    },
    {
      property: "og:description",
      content:
        "AI 驅動的計劃書生成工具，支援多種補助計畫類型，一鍵生成專業計畫書草稿。",
    },
    { property: "og:type", content: "website" },
    { name: "robots", content: "index, follow" },
  ],
});
import {
  callAutoFillApi,
  buildSectionSchema,
  processAutoFillResults,
} from "~/utils/wordImport";
import {
  buildDynamicSections,
  createEmptyDynamicValues,
  makeCompositeKey,
  type DynamicSubFieldKey,
} from "~/utils/dynamicSchema";

definePageMeta({
  middleware: "auth",
});

interface PlanTypeOption {
  id: string;
  title: string;
  subtitle: string;
  description: string;
  category: string;
  tags: string[];
  configNote: string;
  grantName: string;
  templateHint?: string;
  configId?: string;
  templateId?: string;
  icon: string;
  iconBg: string;
  iconColor: string;
}

interface ModeOption {
  id: "interactive" | "generator";
  title: string;
  description: string;
  badge: string;
}

interface BackgroundAttachment {
  id: string;
  name: string;
  type: "word" | "pdf";
  content: string;
  snippet: string;
  size: number;
}

interface AttachmentAutofillResult {
  dynamicFields: Record<string, string>;
  mainIdea: string;
}

interface ProjectMetadataPayload {
  planType: PlanTypeOption | null;
  backgroundEntries: string[];
  backgroundNotes: string;
  prefilledChatAnswers: Record<string, string>;
  mode: ModeOption["id"] | null;
  createdAt: string;
}

const planTypes: PlanTypeOption[] = [
  {
    id: "siir-domestic",
    title: "SIIR 內銷型",
    subtitle: "小型企業創新研發計畫",
    description: "適用於技術服務整合型案。",
    category: "服務業創新",
    tags: ["SIIR", "內銷", "流程升級"],
    configNote: "Grant: SIIR · Template: 內銷既有模板",
    grantName: "SIIR",
    templateHint: "內銷",
    icon: "ph:lightbulb-duotone",
    iconBg: "bg-[#fff2e6]",
    iconColor: "#ff8c55",
  },
  {
    id: "imdp-export",
    title: "IMDP 外銷型",
    subtitle: "服務業創新研發計畫",
    description: "適用於裝置製造與國際型案。",
    category: "外銷拓展",
    tags: ["IMDP", "出口", "品牌國際化"],
    configNote: "Grant: IMDP · Template: Export Master",
    grantName: "IMDP",
    templateHint: "外銷",
    icon: "ph:storefront-duotone",
    iconBg: "bg-[#eef2ff]",
    iconColor: "#4b63ff",
  },
  {
    id: "citd-rnd",
    title: "CITD 研發型",
    subtitle: "傳統產業技術研發計畫",
    description: "適用於製程改良及產品設計。",
    category: "製造研發",
    tags: ["CITD", "研發", "設備投資"],
    configNote: "Grant: CITD · Template: R&D Core",
    grantName: "CITD",
    templateHint: "研發",
    icon: "ph:factory-duotone",
    iconBg: "bg-[#e9f7ef]",
    iconColor: "#22c55e",
  },
  {
    id: "rnd-transform-small",
    title: "研發轉型案 · 九人以下",
    subtitle: "臺北市產業發展獎勵",
    description: "適用於總部設於北市之研發。",
    category: "研發轉型",
    tags: ["轉型", "<9", "快速導入"],
    configNote: "Grant: 研發轉型案 · Template: 小型企業",
    grantName: "研發轉型",
    templateHint: "九人以下",
    icon: "ph:buildings-duotone",
    iconBg: "bg-[#f3ecff]",
    iconColor: "#9b5de5",
  },
  {
    id: "rnd-transform-large",
    title: "研發轉型案 · 十人以上",
    subtitle: "臺北市產業發展獎勵",
    description: "適用於跨部門協同與治理。",
    category: "研發轉型",
    tags: ["轉型", ">10", "治理"],
    configNote: "Grant: 研發轉型案 · Template: 中大型",
    grantName: "研發轉型",
    templateHint: "十人以上",
    icon: "ph:circles-three-plus-duotone",
    iconBg: "bg-[#fef3f2]",
    iconColor: "#f43f5e",
  },
  {
    id: "sbir-local",
    title: "SBIR 地方型",
    subtitle: "小型企業創新研發計畫",
    description: "適用於與地方政府共構示範案。",
    category: "地方創新",
    tags: ["SBIR", "地方", "示範"],
    configNote: "Grant: SBIR Local · Template: Standard",
    grantName: "SBIR",
    templateHint: "地方",
    icon: "ph:map-pin-duotone",
    iconBg: "bg-[#ffeef4]",
    iconColor: "#e11d48",
  },
];

const modeOptions: ModeOption[] = [
  {
    id: "interactive",
    title: "互動模式",
    description:
      "保留更多對話節點，逐步確認每一段輸出，適合需要邊寫邊調整的專案。",
    badge: "聊天導向",
  },
  {
    id: "generator",
    title: "計畫生成模式",
    description:
      "一次輸出完整計畫草稿，適合已準備好資料、希望快速生成初稿的團隊。",
    badge: "快速生成",
  },
];

const router = useRouter();
const {
  success,
  error: notifyError,
  warning: notifyWarning,
} = useNotifications();
const { userId: currentUserId, refreshUser } = useCurrentUser();
onMounted(() => {
  refreshUser();
});
const config = useRuntimeConfig();
const API_BASE_URL = `${config.public.apiBaseUrl}/api`;

const { allConfigs, selectedGrantId, selectedTemplateId, onSelectionChange } =
  usePlanGenerator();

const currentStage = ref(1);
const selectedPlanType = ref<PlanTypeOption | null>(null);
const selectedMode = ref<ModeOption["id"] | null>("interactive");
const planName = ref("計劃草稿");
const planSummary = ref("");
const planBackground = ref("");
const backgroundFiles = ref<BackgroundAttachment[]>([]);
const isDraggingBackground = ref(false);
const isProcessingBackground = ref(false);
const backgroundFileInputRef = ref<HTMLInputElement | null>(null);
const isCreatingProject = ref(false);

// Double-click tracking for plan buttons: two clicks within this threshold
const lastClickedPlanId = ref<string | null>(null);
const lastClickTime = ref<number>(0);
const DOUBLE_CLICK_THRESHOLD = 600; // ms

function handlePlanClick(plan: PlanTypeOption) {
  const now = Date.now();
  if (
    lastClickedPlanId.value === plan.id &&
    now - lastClickTime.value <= DOUBLE_CLICK_THRESHOLD
  ) {
    // treat as double-click: ensure selected and advance
    selectedPlanType.value = plan;
    // reset tracking
    lastClickedPlanId.value = null;
    lastClickTime.value = 0;
    // proceed to next step
    handlePlanTypeConfirm();
    return;
  }

  // single click: select and record timestamp
  selectedPlanType.value = plan;
  lastClickedPlanId.value = plan.id;
  lastClickTime.value = now;
  // clear tracking after threshold to avoid stale state
  setTimeout(() => {
    if (
      lastClickedPlanId.value === plan.id &&
      Date.now() - lastClickTime.value >= DOUBLE_CLICK_THRESHOLD
    ) {
      lastClickedPlanId.value = null;
      lastClickTime.value = 0;
    }
  }, DOUBLE_CLICK_THRESHOLD + 50);
}

const { extractTextFromFile } = useFileExtractor();

async function getUserIdOrNotify() {
  const userId = currentUserId.value || (await refreshUser());
  if (!userId) {
    notifyError("無法取得使用者資訊，請重新登入後再試。");
  }
  return userId;
}

const configsLoaded = computed(() => allConfigs.value.length > 0);
const canConfirmPlanType = computed(
  () => Boolean(selectedPlanType.value) && configsLoaded.value
);

const resolvedTemplateName = computed(() => {
  if (!selectedTemplateId.value) return "";
  const grant = allConfigs.value.find((g) => g.id === selectedGrantId.value);
  return (
    grant?.templates.find((tpl) => tpl.id === selectedTemplateId.value)?.name ||
    ""
  );
});

const canEnterChat = computed(() =>
  Boolean(
    selectedMode.value &&
      planName.value.trim() &&
      planSummary.value.trim() &&
      selectedPlanType.value &&
      selectedGrantId.value &&
      selectedTemplateId.value
  )
);

const modeLabel = computed(() => {
  const target = modeOptions.find((mode) => mode.id === selectedMode.value);
  return target?.title || "";
});

const backgroundSummary = computed(() => {
  const entries: string[] = [];
  const manualNotes = planBackground.value.trim();
  if (manualNotes) {
    entries.push(`背景摘要\n${manualNotes}`);
  }
  backgroundFiles.value.forEach((file) => {
    const content = file.content.trim();
    entries.push(`[附件] ${file.name}\n${content || "（無可解析的文字內容）"}`);
  });
  return entries;
});

const combinedBackgroundNotes = computed(() =>
  backgroundSummary.value.join("\n\n").trim()
);

const prefilledChatAnswers = computed(() => {
  const answers: Record<string, string> = {};
  if (planName.value.trim()) answers["plan_name"] = planName.value.trim();
  if (planSummary.value.trim()) {
    answers["main-idea"] = planSummary.value.trim();
    answers["plan_summary"] = planSummary.value.trim();
  }
  if (combinedBackgroundNotes.value) {
    answers["background_notes"] = combinedBackgroundNotes.value;
  }
  if (selectedPlanType.value) {
    answers["plan_type"] = selectedPlanType.value.title;
  }
  if (selectedMode.value) {
    answers["work_mode"] = modeLabel.value;
  }
  return answers;
});

function buildProjectMetadata(): ProjectMetadataPayload {
  return {
    planType: selectedPlanType.value,
    backgroundEntries: backgroundSummary.value,
    backgroundNotes: planBackground.value.trim(),
    prefilledChatAnswers: prefilledChatAnswers.value,
    mode: selectedMode.value,
    createdAt: new Date().toISOString(),
  };
}

async function runAttachmentAutofill(
  userId: string
): Promise<AttachmentAutofillResult | null> {
  if (!backgroundFiles.value.length) {
    return null;
  }

  const entries: string[] = [];
  const summary = planSummary.value.trim();
  if (summary) {
    entries.push(`【計畫摘要】\n${summary}`);
  }

  backgroundFiles.value.forEach((file) => {
    const body = (file.content || "").trim();
    if (body) {
      entries.push(`【${file.name}】\n${body}`);
    }
  });

  const combinedText = entries.join("\n\n---\n\n").trim();
  if (!combinedText) {
    return null;
  }

  const baseValues = createEmptyDynamicValues();
  const sectionsView = buildDynamicSections(baseValues);
  const sectionsPayload = sectionsView.map((section) => ({
    section_id: section.sectionId,
    section_name: section.sectionName,
    json_schema: buildSectionSchema(section),
  }));

  const filledContent = await callAutoFillApi(
    {
      document_text: combinedText,
      sections: sectionsPayload,
      user_id: userId,
    },
    API_BASE_URL
  );

  const accumulator = { ...baseValues };
  processAutoFillResults(
    filledContent,
    sectionsView,
    (sectionId, propertyKey, subFieldKey, value) => {
      const normalized = (value || "").trim();
      if (!normalized) {
        return;
      }
      const key = makeCompositeKey(
        sectionId,
        propertyKey,
        subFieldKey as DynamicSubFieldKey
      );
      accumulator[key] = normalized;
    },
    () => {}
  );

  const dynamicFields = Object.fromEntries(
    Object.entries(accumulator).filter(([, value]) =>
      Boolean(value && value.trim())
    )
  ) as Record<string, string>;

  const mainIdea =
    filledContent?.main_idea?.content?.project_name_and_summary?.trim() || "";

  if (!Object.keys(dynamicFields).length && !mainIdea) {
    return null;
  }

  return {
    dynamicFields,
    mainIdea,
  };
}

function triggerBackgroundUpload() {
  if (isProcessingBackground.value) {
    notifyWarning("附件解析中，請稍候片刻再試");
    return;
  }
  const input = backgroundFileInputRef.value;
  if (input) {
    input.value = "";
    input.click();
  }
}

function handleBackgroundFileChange(event: Event) {
  const input = event.target as HTMLInputElement | null;
  const files = input?.files ? Array.from(input.files) : [];
  if (input) {
    input.value = "";
  }
  if (files.length) {
    processBackgroundFiles(files);
  }
}

function handleBackgroundDrop(event: DragEvent) {
  isDraggingBackground.value = false;
  const droppedFiles = event.dataTransfer?.files;
  if (!droppedFiles || !droppedFiles.length) return;
  processBackgroundFiles(Array.from(droppedFiles));
}

async function processBackgroundFiles(files: File[]) {
  if (isProcessingBackground.value) {
    notifyWarning("附件解析中，請稍候片刻再試");
    return;
  }
  const classified = files
    .map((file) => ({ file, type: detectBackgroundType(file) }))
    .filter((item): item is { file: File; type: "word" | "pdf" } =>
      Boolean(item.type)
    );
  if (!classified.length) {
    notifyWarning("僅支援 Word (.docx) 與 PDF 檔案");
    return;
  }
  if (classified.length < files.length) {
    notifyWarning("部分檔案格式不支援，僅匯入 Word/PDF");
  }
  isProcessingBackground.value = true;
  try {
    for (const item of classified) {
      await importBackgroundFile(item.file, item.type);
    }
  } finally {
    isProcessingBackground.value = false;
  }
}

function detectBackgroundType(file: File): "word" | "pdf" | null {
  const name = file.name.toLowerCase();
  if (name.endsWith(".docx")) return "word";
  if (name.endsWith(".pdf")) return "pdf";
  const mime = (file.type || "").toLowerCase();
  if (mime.includes("word")) return "word";
  if (mime.includes("pdf")) return "pdf";
  return null;
}

async function importBackgroundFile(file: File, type: "word" | "pdf") {
  try {
    const rawText = await extractTextFromFile(file);
    const normalized = normalizeBackgroundText(rawText);
    const snippet = normalized
      ? `${normalized.slice(0, 200)}${normalized.length > 200 ? "..." : ""}`
      : "未偵測到可用文字內容";
    backgroundFiles.value = [
      ...backgroundFiles.value,
      {
        id: createAttachmentId(),
        name: file.name,
        type,
        content: normalized,
        snippet,
        size: file.size,
      },
    ];
    success(`已匯入 ${file.name}`);
  } catch (error: any) {
    console.error("failed to import background file", error);
    notifyError(`解析 ${file.name} 失敗：${error?.message || "請稍後再試"}`);
  }
}

function normalizeBackgroundText(value: string) {
  return (value || "")
    .replace(/\r\n/g, "\n")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

function createAttachmentId() {
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function removeBackgroundAttachment(id: string) {
  backgroundFiles.value = backgroundFiles.value.filter(
    (file) => file.id !== id
  );
}

function clearBackgroundAttachments() {
  backgroundFiles.value = [];
}

function selectPlanType(plan: PlanTypeOption) {
  selectedPlanType.value = plan;
}

function resolvePlanConfig(plan: PlanTypeOption | null) {
  if (!plan || !allConfigs.value.length) return null;
  let grant = null;
  if (plan.configId) {
    grant = allConfigs.value.find((item) => item.id === plan.configId) || null;
  }
  if (!grant) {
    grant =
      allConfigs.value.find((item) =>
        item.name.toLowerCase().includes(plan.grantName.toLowerCase())
      ) || null;
  }
  if (!grant) {
    grant = allConfigs.value[0] || null;
  }
  if (!grant) return null;

  let template = null;
  if (plan.templateId) {
    template =
      grant.templates.find((tpl) => tpl.id === plan.templateId) || null;
  }
  if (!template && plan.templateHint) {
    template =
      grant.templates.find((tpl) =>
        tpl.name.toLowerCase().includes(plan.templateHint!.toLowerCase())
      ) || null;
  }
  if (!template) {
    template = grant.templates[0] || null;
  }
  if (!template) return null;

  return {
    grantId: grant.id,
    templateId: template.id,
  };
}

function handlePlanTypeConfirm() {
  if (!selectedPlanType.value) {
    notifyWarning("請先選擇計畫類型");
    return;
  }
  const configSelection = resolvePlanConfig(selectedPlanType.value);
  if (!configSelection) {
    notifyError("找不到對應的 Config，請確認 API 是否已回傳資料");
    return;
  }
  onSelectionChange(configSelection);
  // planName.value = selectedPlanType.value.title;
  currentStage.value = 2;
}

function backToStage(stage: number) {
  currentStage.value = stage;
}

async function enterChatStage() {
  if (!canEnterChat.value || isProcessingBackground.value) {
    notifyWarning("請先完成模式與背景資訊填寫");
    return;
  }
  const userId = await getUserIdOrNotify();
  if (!userId || isCreatingProject.value) {
    return;
  }

  const metadata = buildProjectMetadata();
  isCreatingProject.value = true;
  let storedAnswerPayload: Record<string, any> | null = null;
  try {
    if (backgroundFiles.value.length) {
      try {
        const autofillResult = await runAttachmentAutofill(userId);
        if (autofillResult) {
          //直接存入stored answer
          if (selectedMode.value === "generator") {
            storedAnswerPayload = {
              user_input: {
                main_idea:
                  autofillResult.mainIdea ||
                  planSummary.value.trim() ||
                  selectedPlanType.value?.title ||
                  "",
                dynamic_fields: autofillResult.dynamicFields,
              },
            };
          } else {
            storedAnswerPayload = {
              chat_answers: autofillResult.dynamicFields,
            };
          }
        }
      } catch (autofillError) {
        console.error("Failed to auto-fill dynamic sections", autofillError);
        notifyWarning(
          "附件解析完成，但自動填寫欄位失敗，將以空白欄位建立工作區。"
        );
      }
    }

    const {
      data: { session },
    } = await supabase.auth.getSession();

    if (!session?.access_token) {
      throw new Error("請先登入");
    }

    const response = await fetch(`${API_BASE_URL}/projects`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${session.access_token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        mode: selectedMode.value || "interactive",
        title:
          planName.value.trim() ||
          selectedPlanType.value?.title ||
          "未命名計畫案",
        description: planSummary.value.trim() || "尚未填寫摘要",
        saved_plan: [],
        conversation_history: [],
        stored_answer: storedAnswerPayload || {},
        grant_id: selectedGrantId.value || null,
        template_id: selectedTemplateId.value || null,
        plan_type_id: selectedPlanType.value?.id || null,
        plan_metadata: metadata,
      }),
    });

    if (!response.ok) {
      const detail = await response.text();
      throw new Error(detail || "建立計畫失敗");
    }

    const record = await response.json();
    success("已建立計畫並準備前往工作區");
    router.push(`/projects/${record.id}`);
  } catch (error: any) {
    console.error("Failed to create project", error);
    notifyError(error?.message || "建立計畫失敗，請稍後再試");
  } finally {
    isCreatingProject.value = false;
  }
}
</script>
