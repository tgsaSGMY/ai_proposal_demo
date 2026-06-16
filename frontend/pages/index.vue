<template>
  <ClientOnly>
    <div class="h-screen flex flex-col">
      <!-- Loading -->
      <div v-if="isInitializing" class="flex-1 flex items-center justify-center text-gray-500">
        <div class="text-center">
          <div class="inline-block h-8 w-8 animate-spin rounded-full border-4 border-rose-200 border-t-rose-500"></div>
          <p class="mt-3 text-sm">正在準備您的計畫書工作區…</p>
        </div>
      </div>

      <!-- Setup error -->
      <div v-else-if="setupError" class="flex-1 flex items-center justify-center px-6">
        <div class="max-w-md text-center">
          <p class="text-base text-rose-600 font-semibold">無法載入體驗</p>
          <p class="mt-2 text-sm text-gray-600">{{ setupError }}</p>
          <button class="mt-4 rounded-lg bg-rose-500 px-4 py-2 text-sm font-semibold text-white hover:bg-rose-600" @click="initialize">
            重試
          </button>
        </div>
      </div>

      <!-- Chat workspace -->
      <DemoChatbox
        v-else
        :grant-id="grantId"
        :template-id="templateId"
        :grant-name="grantName"
        :template-name="templateName"
        :all-questions="allQuestions"
        :session-id="sessionId"
        :interaction-count="interactionCount"
        :interaction-limit="interactionLimit"
        :chat-limit-reached="chatLimitReached"
        :generation-limit-reached="generationLimitReached"
        :download-limit-reached="downloadLimitReached"
        :has-generated-docx="hasGeneratedDocx"
        :conversation-history="conversationHistory"
        :stored-answers="storedAnswers"
        :register-url="registerUrl"
        :project-title="projectTitle"
        :project-summary="projectSummary"
        :sections="sections"
        :candidate-plan="candidatePlan"
        :final-plan="finalPlanContent"
        :saved-plan-versions="savedPlanVersions"
        :section-versions="sectionVersions"
        @messages-updated="handleMessagesUpdated"
        @question-answers-updated="handleAnswersUpdated"
        @ai-response-complete="handleAiResponseComplete"
        @generate-plan="handleGeneratePlan"
        @download-completed="handleDownloadCompleted"
        @update-project-title="handleUpdateProjectTitle"
        @finalize-candidates="handleFinalizeCandidates"
        @request-version-update="handleVersionRevision"
        @register="handleRegister"
      />
    </div>

    <!-- Register prompt modal -->
    <DemoRegisterModal
      v-model:is-open="showRegisterModal"
      :interaction-count="interactionCount"
      :interaction-limit="interactionLimit"
      :register-url="registerUrl"
      :session-id="sessionId"
      :project-title="projectTitle"
      @close="showRegisterModal = false"
      @update-title="handleUpdateProjectTitle"
    />

    <!-- Global confirm + notifications (rendered by layout or App.vue) -->
  </ClientOnly>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from "vue";
import DemoChatbox from "~/components/chat/DemoChatbox.vue";
import DemoRegisterModal from "~/components/chat/helper/DemoRegisterModal.vue";
import { useLoading } from "~/composables/useLoading";
import { useNotifications } from "~/composables/useNotifications";

const { show: showLoading, hide: hideLoading } = useLoading();
const { success, error: notifyError } = useNotifications();

// SSR disabled for this page (window, WebSocket)
definePageMeta({
  ssr: false,
});

const config = useRuntimeConfig();
const apiBaseUrl = `${config.public.apiBaseUrl}/api`;

interface Question {
  id: string;
  label: string;
  prompt: string;
}

const isInitializing = ref(true);
const setupError = ref<string | null>(null);

const sessionId = ref("");
const grantId = ref("");
const templateId = ref("");
const grantName = ref("");
const templateName = ref("");
const allQuestions = ref<Question[]>([]);
const conversationHistory = ref<any[]>([]);
const storedAnswers = ref<Record<string, string>>({});

const interactionCount = ref(0);
const interactionLimit = ref(20);
const chatLimitReached = ref(false);
const generationLimitReached = ref(false);
const downloadLimitReached = ref(false);
const hasGeneratedDocx = ref(false);
  const showRegisterModal = ref(false);
  const registerUrl = ref(config.public.platformHomeUrl || "https://aiproposal.tgsa.com.tw/api/external-auth/redirect");
  const projectTitle = ref("計畫草稿");
  const projectSummary = ref("");
  const sections = ref<any[]>([]);
  const candidatePlan = ref<Record<string, any>>({});
  const finalPlanContent = ref<Record<string, any>>({});
  const savedPlanVersions = ref<any[]>([]);
  const sectionVersions = ref<Record<string, number>>({});

function deriveQuestions(sections: any[]): Question[] {
  const result: Question[] = [];
  for (const section of sections || []) {
    const schema = section?.json_schema;
    const props = schema?.properties;
    if (!props || typeof props !== "object") continue;
    for (const [key, raw] of Object.entries(props)) {
      const def = (raw || {}) as { title?: string; description?: string };
      const label = def.title || key;
      result.push({
        id: `${section.id}::${key}`,
        label: `${section.name}｜${label}`,
        prompt: def.description || label,
      });
    }
  }
  return result;
}

function buildQuestionsFromDynamicFields(dynamicSections: any[]): Question[] {
  const result: Question[] = [];
  for (const section of dynamicSections || []) {
    for (const field of section.fields || []) {
      result.push({
        id: `${section.section_key}::${field.field_key}`,
        label: `${section.title}｜${field.title}`,
        prompt: field.description || field.title,
      });
    }
  }
  return result;
}

async function loadCatalogAndSession() {
  const [configResp, demoResp] = await Promise.all([
    fetch(`${apiBaseUrl}/config`, { credentials: "include" }),
    fetch(`${apiBaseUrl}/demo`, { credentials: "include" }),
  ]);

  if (!configResp.ok) {
    throw new Error(`/api/config returned ${configResp.status}`);
  }
  if (!demoResp.ok) {
    throw new Error(`/api/demo returned ${demoResp.status}`);
  }

  const catalog = (await configResp.json()) as any[];
  const demo = (await demoResp.json()) as Record<string, any>;

  sessionId.value = demo.session_id;

  // Optionally fetch demo status for updated limits (defensive: may 404 until backend ready)
  try {
    const statusResp = await fetch(`${apiBaseUrl}/demo/status`, { credentials: "include" });
    if (statusResp.ok) {
      const status = await statusResp.json();
      interactionCount.value = status.interaction_count ?? demo.interaction_count ?? 0;
      interactionLimit.value = status.interaction_limit ?? 15;
      chatLimitReached.value = status.chat_limit_reached ?? (interactionCount.value >= interactionLimit.value);
      generationLimitReached.value = status.generation_limit_reached ?? false;
      downloadLimitReached.value = status.download_limit_reached ?? false;
      hasGeneratedDocx.value = status.has_generated_docx ?? demo.has_generated_docx ?? false;
      if (status.register_url) registerUrl.value = status.register_url;
    } else {
      interactionCount.value = demo.interaction_count ?? 0;
      interactionLimit.value = 20;
      chatLimitReached.value = interactionCount.value >= interactionLimit.value;
      hasGeneratedDocx.value = demo.has_generated_docx ?? false;
    }
  } catch {
    interactionCount.value = demo.interaction_count ?? 0;
    interactionLimit.value = 20;
    chatLimitReached.value = interactionCount.value >= interactionLimit.value;
    hasGeneratedDocx.value = demo.has_generated_docx ?? false;
  }

  // Template selection strategy:
  // 1. If NUXT_PUBLIC_DEMO_GRANT_ID and NUXT_PUBLIC_DEMO_TEMPLATE_ID are set
  //    in the frontend .env, ALWAYS use those values — no fallback.
  // 2. If they are not set yet (empty), fall back to the old behavior
  //    (session value, then first in catalog) so the demo keeps working
  //    until the operator populates the environment variables.
  const configuredGrantId = config.public.demoGrantId as string;
  const configuredTemplateId = config.public.demoTemplateId as string;

  let chosenGrant: any;
  let chosenTemplate: any;

  if (configuredGrantId && configuredTemplateId) {
    // STRICT MODE: env-configured IDs always win. No fallback.
    chosenGrant = catalog.find((g) => g.id === configuredGrantId);
    chosenTemplate = chosenGrant?.templates?.find((t: any) => t.id === configuredTemplateId);
    if (!chosenGrant || !chosenTemplate) {
      throw new Error(
        `No template found for grant_id="${configuredGrantId}" template_id="${configuredTemplateId}"`
      );
    }
  } else {
    // BACKWARD-COMPATIBLE MODE: env vars not set yet — use session or first-in-catalog.
    // TODO: Remove this branch once DEMO_GRANT_ID / DEMO_TEMPLATE_ID are configured in .env
    chosenGrant = catalog.find((g) => g.id === demo.grant_id);
    chosenTemplate = chosenGrant?.templates?.find((t: any) => t.id === demo.template_id);
    if (!chosenGrant || !chosenTemplate) {
      chosenGrant = catalog[0];
      chosenTemplate = chosenGrant?.templates?.[0];
    }
  }

  if (!chosenGrant || !chosenTemplate) {
    throw new Error("No grant templates available — apply demo_migration.sql and seed the catalog.");
  }

  grantId.value = chosenGrant.id;
  templateId.value = chosenTemplate.id;
  grantName.value = chosenGrant.name || "";
  templateName.value = chosenTemplate.name || "";

  // --- Dynamic fields support (production parity) ---
  // The full platform's _builder configures questions via dynamic_sections +
  // dynamic_fields tables. When those exist, use them instead of the static
  // sections.json_schema so the demo matches the production experience.
  let dynamicFields: any[] = [];
  try {
    const dynResp = await fetch(
      `${apiBaseUrl}/demo/dynamic-fields?grant_id=${grantId.value}&template_id=${templateId.value}`,
      { credentials: "include" }
    );
    if (dynResp.ok) {
      const dynData = await dynResp.json();
      dynamicFields = dynData.sections || [];
    }
  } catch {
    // ignore — will fall back to deriveQuestions
  }

  if (dynamicFields.length > 0) {
    allQuestions.value = buildQuestionsFromDynamicFields(dynamicFields);
    // KEEP static sections for plan generation / candidate selector compatibility.
    // The backend generate_plan returns candidates keyed by static section.id
    // (e.g. "company_overview"), so the sections prop must use those same IDs.
    sections.value = Array.isArray(chosenTemplate.sections) ? chosenTemplate.sections : [];
  } else {
    // FALLBACK: template has no dynamic fields — use static json_schema
    allQuestions.value = deriveQuestions(chosenTemplate.sections);
    sections.value = Array.isArray(chosenTemplate.sections) ? chosenTemplate.sections : [];
  }

  const savedPlan = demo.saved_plan;
  if (Array.isArray(savedPlan)) {
    savedPlanVersions.value = savedPlan;
    const latest = savedPlan[savedPlan.length - 1];
    if (latest && typeof latest === "object" && latest.data) {
      finalPlanContent.value = latest.data as Record<string, any>;
    }
  } else if (savedPlan && typeof savedPlan === "object") {
    finalPlanContent.value = savedPlan as Record<string, any>;
  }

  if (demo.grant_id !== grantId.value || demo.template_id !== templateId.value) {
    await fetch(`${apiBaseUrl}/demo`, {
      method: "PUT",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ grant_id: grantId.value, template_id: templateId.value }),
    });
  }

  if (Array.isArray(demo.conversation_history)) {
    conversationHistory.value = demo.conversation_history;
  }
  if (demo.stored_answer?.chat_answers) {
    storedAnswers.value = demo.stored_answer.chat_answers;
  }
  if (demo.title) {
    projectTitle.value = demo.title;
  }
  if (demo.section_versions) {
    sectionVersions.value = demo.section_versions;
  }
}

async function initialize() {
  setupError.value = null;
  isInitializing.value = true;
  try {
    await loadCatalogAndSession();
  } catch (err: any) {
    console.error(err);
    setupError.value = err?.message || "Unknown error";
  } finally {
    isInitializing.value = false;
  }
}

// -- Event handlers from DemoChatbox --
function handleMessagesUpdated(newMessages: any[]) {
  // Persist to backend if desired (debounced)
  // For now, the WebSocket handler in DemoChatbox already sends state to WS
  // and the backend saves it. This hook is for any parent-side logic.
}

function handleAnswersUpdated(newAnswers: Record<string, string>) {
  // Same as above
}

function handleAiResponseComplete() {
  // Could refresh status from backend to get updated interaction count
  refreshStatus().catch(() => {});
}

async function refreshStatus() {
  try {
    const resp = await fetch(`${apiBaseUrl}/demo/status`, { credentials: "include" });
    if (!resp.ok) return;
    const status = await resp.json();
    interactionCount.value = status.interaction_count ?? interactionCount.value;
    interactionLimit.value = status.interaction_limit ?? interactionLimit.value;
    chatLimitReached.value = status.chat_limit_reached ?? (interactionCount.value >= interactionLimit.value);
    generationLimitReached.value = status.generation_limit_reached ?? false;
    downloadLimitReached.value = status.download_limit_reached ?? false;
    hasGeneratedDocx.value = status.has_generated_docx ?? hasGeneratedDocx.value;
  } catch {
    // ignore
  }
}

function handleRegister() {
  chatLimitReached.value = true;
  generationLimitReached.value = true;
  downloadLimitReached.value = true;
  // Also try to refresh status to get accurate counts from backend
  refreshStatus().catch(() => {});
}

watch(chatLimitReached, (reached) => {
  if (reached) showRegisterModal.value = true;
}, { immediate: true });

async function handleDownloadCompleted() {
  await refreshStatus().catch(() => {});
}

async function handleUpdateProjectTitle(name: string) {
  if (name) {
    projectTitle.value = name;
    success("已更新專案名稱");
    // Persist title to backend so it survives migration
    try {
      await fetch(`${apiBaseUrl}/demo`, {
        method: "PUT",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: name }),
      });
    } catch (err) {
      console.warn("Failed to persist title to demo session", err);
    }
  }
}

function transformPlanCandidates(rawData: Record<string, any>) {
  const processed: Record<string, any> = {};
  if (!rawData || typeof rawData !== "object") return processed;
  Object.entries(rawData).forEach(([sectionId, candidates]) => {
    if (!Array.isArray(candidates)) return;
    processed[sectionId] = (candidates as any[]).map((candidate: any) => ({
      content:
        candidate?.raw_json_content ?? candidate?.content ?? candidate ?? null,
      error: candidate?.error || null,
    }));
  });
  return processed;
}

async function handleGeneratePlan(payload: {
  grantId: string;
  templateId: string;
  prompt: string;
}) {
  if (!payload?.prompt || !payload.grantId || !payload.templateId) return;
  finalPlanContent.value = {};
  candidatePlan.value = {};
  showLoading("正在生成計畫書...", true);
  try {
    const resp = await fetch(`${apiBaseUrl}/generate_plan`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        grant: payload.grantId,
        template: payload.templateId,
        user_input: payload.prompt,
        num_candidates: 2,
      }),
    });
    if (!resp.ok) {
      const text = await resp.text();
      throw new Error(`伺服器錯誤 (${resp.status}): ${text}`);
    }
    const rawData = await resp.json();
    candidatePlan.value = transformPlanCandidates(rawData);
    success("計畫書草稿已生成！");
    await refreshStatus().catch(() => {});
  } catch (err: any) {
    console.error("生成計畫書失敗", err);
    notifyError(`生成失敗: ${err?.message || "未知錯誤"}`);
  } finally {
    hideLoading();
  }
}

async function handleVersionRevision(payload: { version: any }) {
  if (!payload?.version?.data) {
    notifyError("找不到這個版本的內容，無法更新。");
    return;
  }
  if (!grantId.value || !templateId.value) {
    notifyError("請先完成基本設定後再進行版本更新。");
    return;
  }

  showLoading("正在優化計畫版本...", true);
  finalPlanContent.value = {};
  candidatePlan.value = {};

  try {
    const resp = await fetch(`${apiBaseUrl}/revise_plan_version`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        grant: grantId.value,
        template: templateId.value,
        current_version: payload.version.data,
        stored_answer: { chat_answers: storedAnswers.value },
        project_title: projectTitle.value || "",
        project_summary: projectSummary.value || "",
        num_candidates: 2,
      }),
    });
    if (!resp.ok) {
      const text = await resp.text();
      throw new Error(`伺服器錯誤 (${resp.status}): ${text}`);
    }
    const rawData = await resp.json();
    candidatePlan.value = transformPlanCandidates(rawData);
    success("新版候選內容已生成！");
  } catch (err: any) {
    console.error("版本更新失敗", err);
    notifyError(`版本更新失敗: ${err?.message || "未知錯誤"}`);
  } finally {
    hideLoading();
  }
}

async function handleFinalizeCandidates(payload: {
  selected: Record<string, any>;
  rejected?: Record<string, any>;
}) {
  const selected = payload?.selected || {};
  const newPlanContent: Record<string, { content?: string; error?: string }> = {};
  Object.entries(selected).forEach(([sectionId, candidate]) => {
    if (candidate && (candidate as any).content) {
      newPlanContent[sectionId] = { content: (candidate as any).content };
    } else {
      newPlanContent[sectionId] = {
        error: (candidate as any)?.error || "No content",
      };
    }
  });
  finalPlanContent.value = newPlanContent;
  candidatePlan.value = {};

  const versionNumber = savedPlanVersions.value.length + 1;
  const newVersion = {
    number: versionNumber,
    title: `版本 ${versionNumber}`,
    timestamp: new Date().toISOString(),
    data: newPlanContent,
  };
  const updatedVersions = [...savedPlanVersions.value, newVersion];
  savedPlanVersions.value = updatedVersions;

  try {
    await fetch(`${apiBaseUrl}/demo`, {
      method: "PUT",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ saved_plan: updatedVersions, has_generated_docx: true, title: projectTitle.value }),
    });
    hasGeneratedDocx.value = true;
    generationLimitReached.value = true;
    success("已選擇方案並填充到結果中！");
  } catch (err) {
    console.error("Failed to persist selected plan to demo session", err);
    notifyError("儲存計畫失敗，請稍後再試");
  }
}

onMounted(() => {
  void initialize();
});
</script>