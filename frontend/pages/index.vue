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
        :limit-reached="limitReached"
        :has-generated-docx="hasGeneratedDocx"
        :conversation-history="conversationHistory"
        :stored-answers="storedAnswers"
        :register-url="registerUrl"
        @messages-updated="handleMessagesUpdated"
        @question-answers-updated="handleAnswersUpdated"
        @ai-response-complete="handleAiResponseComplete"
        @request-generation="handleRequestGeneration"
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
      @close="showRegisterModal = false"
    />

    <!-- Global confirm + notifications (rendered by layout or App.vue) -->
  </ClientOnly>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import DemoChatbox from "~/components/chat/DemoChatbox.vue";
import DemoRegisterModal from "~/components/chat/helper/DemoRegisterModal.vue";

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
const interactionLimit = ref(15);
const limitReached = ref(false);
const hasGeneratedDocx = ref(false);
const showRegisterModal = ref(false);
const registerUrl = ref(config.public.platformHomeUrl || "https://aiproposal.tgsa.com.tw/api/external-auth/redirect");

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
      limitReached.value = status.limit_reached ?? (interactionCount.value >= interactionLimit.value);
      hasGeneratedDocx.value = status.has_generated_docx ?? demo.has_generated_docx ?? false;
      if (status.register_url) registerUrl.value = status.register_url;
    } else {
      interactionCount.value = demo.interaction_count ?? 0;
      interactionLimit.value = 15;
      limitReached.value = interactionCount.value >= interactionLimit.value;
      hasGeneratedDocx.value = demo.has_generated_docx ?? false;
    }
  } catch {
    interactionCount.value = demo.interaction_count ?? 0;
    interactionLimit.value = 15;
    limitReached.value = interactionCount.value >= interactionLimit.value;
    hasGeneratedDocx.value = demo.has_generated_docx ?? false;
  }

  let chosenGrant = catalog.find((g) => g.id === demo.grant_id);
  let chosenTemplate = chosenGrant?.templates?.find((t: any) => t.id === demo.template_id);
  if (!chosenGrant || !chosenTemplate) {
    chosenGrant = catalog[0];
    chosenTemplate = chosenGrant?.templates?.[0];
  }

  if (!chosenGrant || !chosenTemplate) {
    throw new Error("No grant templates available — apply demo_migration.sql and seed the catalog.");
  }

  grantId.value = chosenGrant.id;
  templateId.value = chosenTemplate.id;
  grantName.value = chosenGrant.name || "";
  templateName.value = chosenTemplate.name || "";
  allQuestions.value = deriveQuestions(chosenTemplate.sections);

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
    limitReached.value = status.limit_reached ?? (interactionCount.value >= interactionLimit.value);
    hasGeneratedDocx.value = status.has_generated_docx ?? hasGeneratedDocx.value;
  } catch {
    // ignore
  }
}

function handleRegister() {
  limitReached.value = true;
  showRegisterModal.value = true;
  // Also try to refresh status to get accurate counts from backend
  refreshStatus().catch(() => {});
}

async function handleRequestGeneration(payload: any) {
  // If a report has already been generated, try to re-download it.
  if (hasGeneratedDocx.value) {
    try {
      const resp = await fetch(`${apiBaseUrl}/demo/finalize`, {
        method: "POST",
        credentials: "include",
      });
      if (resp.ok) {
        const blob = await resp.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `${grantName.value || "plan"}_draft.docx`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        return;
      }
    } catch {
      // fall through to register modal
    }
  }
  // Backend generation pipeline is being built by colleague.
  // Show the register modal as a soft notice until endpoints are ready.
  showRegisterModal.value = true;
}

onMounted(() => {
  void initialize();
});
</script>