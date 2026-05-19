<template>
  <ClientOnly>
    <div class="min-h-screen bg-gray-50 flex flex-col">
      <!-- Header -->
      <header class="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <img
            src="/AI補助引擎_Logo_留邊.png"
            alt="AI 補助引擎"
            class="h-10 w-auto pointer-events-none select-none"
          />
          <span class="hidden sm:inline-flex items-center gap-2 rounded-full bg-rose-50 px-3 py-1 text-xs font-semibold text-rose-600">
            試用版 · 免註冊體驗
          </span>
        </div>
        <div v-if="grantName" class="text-sm text-gray-500">
          目前體驗：<span class="font-semibold text-gray-800">{{ grantName }}</span>
        </div>
      </header>

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
          <button
            class="mt-4 rounded-lg bg-rose-500 px-4 py-2 text-sm font-semibold text-white hover:bg-rose-600"
            @click="initialize"
          >
            重試
          </button>
        </div>
      </div>

      <!-- Chat workspace -->
      <main v-else class="flex-1 flex flex-col overflow-hidden">
        <div
          ref="messagesContainer"
          class="flex-1 overflow-y-auto px-4 sm:px-6 py-6"
        >
          <div class="mx-auto max-w-3xl space-y-4">
            <div
              v-for="(message, idx) in visibleMessages"
              :key="idx"
              class="flex"
              :class="message.role === 'user' ? 'justify-end' : 'justify-start'"
            >
              <div
                class="max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap"
                :class="
                  message.role === 'user'
                    ? 'bg-rose-500 text-white rounded-br-sm'
                    : 'bg-white border border-gray-200 text-gray-800 rounded-bl-sm shadow-sm'
                "
              >
                {{ stripHiddenBlock(message.content) }}
                <span
                  v-if="message.isStreaming"
                  class="ml-1 inline-block h-2 w-2 animate-pulse rounded-full bg-rose-400 align-middle"
                ></span>
              </div>
            </div>
          </div>
        </div>

        <!-- Counter + composer -->
        <div class="border-t border-gray-200 bg-white px-4 sm:px-6 py-4">
          <div class="mx-auto max-w-3xl">
            <p class="mb-2 text-xs text-gray-500">
              已使用 <span class="font-semibold text-gray-800">{{ interactionCount }}</span> / {{ interactionLimit }} 次互動
              <span v-if="!limitReached" class="text-gray-400">— 試用結束後可註冊以繼續完整體驗</span>
            </p>
            <form class="flex items-end gap-2" @submit.prevent="sendMessage">
              <textarea
                v-model="userInput"
                rows="2"
                placeholder="輸入您的回覆…"
                class="flex-1 resize-none rounded-xl border border-gray-300 px-3 py-2 text-sm focus:border-rose-400 focus:outline-none focus:ring-2 focus:ring-rose-200"
                :disabled="limitReached || isStreaming"
                @keydown.enter.exact.prevent="sendMessage"
              ></textarea>
              <button
                type="submit"
                class="rounded-xl bg-rose-500 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-rose-600 disabled:cursor-not-allowed disabled:bg-gray-300"
                :disabled="!canSend"
              >
                送出
              </button>
            </form>
          </div>
        </div>
      </main>

      <!-- Register prompt modal -->
      <div
        v-if="showRegisterModal"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4"
      >
        <div class="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl">
          <h2 class="text-lg font-bold text-gray-900">
            喜歡這次的體驗嗎？
          </h2>
          <p class="mt-3 text-sm text-gray-600 leading-relaxed">
            您已完成 {{ interactionLimit }} 次試用互動。
            註冊免費帳號即可繼續完成這份計畫書，並使用完整的版本管理與 Word 匯出功能。
          </p>
          <div class="mt-6 flex flex-col gap-2 sm:flex-row sm:justify-end">
            <button
              class="rounded-lg border border-gray-300 px-4 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-50"
              @click="showRegisterModal = false"
            >
              再看看
            </button>
            <a
              :href="registerHref"
              class="rounded-lg bg-rose-500 px-4 py-2 text-center text-sm font-semibold text-white hover:bg-rose-600"
            >
              立即註冊繼續使用
            </a>
          </div>
        </div>
      </div>
    </div>
  </ClientOnly>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from "vue";

definePageMeta({
  layout: false,
  ssr: false,
});

const config = useRuntimeConfig();
const apiBaseUrl = `${config.public.apiBaseUrl}/api`;

interface ChatMessage {
  role: "user" | "assistant" | "system";
  content: string;
  isStreaming?: boolean;
}

interface Question {
  id: string;
  label: string;
  prompt: string;
}

const isInitializing = ref(true);
const setupError = ref<string | null>(null);

const sessionId = ref<string | null>(null);
const grantId = ref<string | null>(null);
const templateId = ref<string | null>(null);
const grantName = ref("");
const templateName = ref("");
const allQuestions = ref<Question[]>([]);

const messages = ref<ChatMessage[]>([]);
const userInput = ref("");
const isStreaming = ref(false);

const interactionCount = ref(0);
const interactionLimit = ref(10);
const limitReached = ref(false);
const showRegisterModal = ref(false);
const registerUrl = ref<string | null>(null);

const messagesContainer = ref<HTMLDivElement | null>(null);
let ws: WebSocket | null = null;

const visibleMessages = computed(() =>
  messages.value.filter((m) => m.role !== "system"),
);

const canSend = computed(
  () => !limitReached.value && !isStreaming.value && userInput.value.trim().length > 0,
);

// The AI sometimes appends a `【回復結束】【隱藏回復欄位+答案】...【隱藏回復結束】`
// machine-readable block. Hide it from the chat bubble.
function stripHiddenBlock(content: string): string {
  return content.replace(/【回復結束】【隱藏回復欄位\+答案】[\s\S]*?【隱藏回復結束】/g, "").trim();
}

const registerHref = computed(() => {
  if (!registerUrl.value) return "#";
  const url = new URL(registerUrl.value);
  if (sessionId.value) {
    url.searchParams.set("ref", sessionId.value);
  }
  return url.toString();
});

// Flatten the catalog's sections[].json_schema into a list of questions the
// chat-guidance backend expects. Each property in a section's schema becomes
// one question with a `sectionId::propertyKey` id.
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

  // Pick whichever grant/template the demo row already references; otherwise
  // default to the first one in the catalog.
  let chosenGrant = catalog.find((g) => g.id === demo.grant_id);
  let chosenTemplate = chosenGrant?.templates?.find(
    (t: any) => t.id === demo.template_id,
  );
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

  // If the demo row doesn't yet remember which template the visitor is on,
  // pin it so the WS reconnect can short-circuit.
  if (demo.grant_id !== grantId.value || demo.template_id !== templateId.value) {
    await fetch(`${apiBaseUrl}/demo`, {
      method: "PUT",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ grant_id: grantId.value, template_id: templateId.value }),
    });
  }

  // Re-hydrate prior conversation if any.
  if (Array.isArray(demo.conversation_history)) {
    messages.value = demo.conversation_history.map((entry: any) => ({
      role: entry.role,
      content: entry.content || "",
    }));
  }
}

function buildWebsocketUrl(): string {
  const rawApiBase = config.public.apiBaseUrl || "";
  let wsProtocol = window.location.protocol === "https:" ? "wss" : "ws";
  let wsHost = window.location.host;
  let wsPathPrefix = "";

  if (rawApiBase.startsWith("http://") || rawApiBase.startsWith("https://")) {
    const parsed = new URL(rawApiBase);
    wsProtocol = parsed.protocol === "https:" ? "wss" : "ws";
    wsHost = parsed.host;
    wsPathPrefix = parsed.pathname.replace(/\/+$/, "");
  } else if (rawApiBase) {
    wsPathPrefix = (rawApiBase.startsWith("/") ? rawApiBase : `/${rawApiBase}`).replace(
      /\/+$/,
      "",
    );
  }

  const path = `${wsPathPrefix}/api/ws/chat_guidance`.replace(/\/{2,}/g, "/");
  return `${wsProtocol}://${wsHost}${path}`;
}

function openWebSocket() {
  if (ws && ws.readyState !== WebSocket.CLOSED) {
    ws.close();
  }
  ws = new WebSocket(buildWebsocketUrl());

  ws.onopen = () => {
    const payload = {
      grant_id: grantId.value,
      template_id: templateId.value,
      grant_name: grantName.value,
      template_name: templateName.value,
      project_title: templateName.value,
      project_summary: "",
      all_questions: allQuestions.value,
      current_answers: {},
      current_answers_meta: {},
      history: messages.value.map((m) => ({ role: m.role, content: m.content })),
    };
    ws?.send(JSON.stringify(payload));
  };

  ws.onmessage = (event) => {
    let msg: any;
    try {
      msg = JSON.parse(event.data);
    } catch {
      return;
    }
    handleServerEvent(msg);
  };

  ws.onerror = () => {
    isStreaming.value = false;
  };

  ws.onclose = () => {
    isStreaming.value = false;
  };
}

function handleServerEvent(msg: any) {
  switch (msg.event) {
    case "ready":
      interactionCount.value = msg.interaction_count ?? 0;
      interactionLimit.value = msg.interaction_limit ?? interactionLimit.value;
      if (interactionCount.value >= interactionLimit.value) {
        limitReached.value = true;
        showRegisterModal.value = true;
      }
      break;
    case "chunk_start":
      isStreaming.value = true;
      messages.value.push({ role: "assistant", content: "", isStreaming: true });
      scrollToBottom();
      break;
    case "chunk": {
      const last = messages.value[messages.value.length - 1];
      if (last && last.role === "assistant" && last.isStreaming) {
        last.content += msg.data || "";
        scrollToBottom();
      }
      break;
    }
    case "done": {
      const last = messages.value[messages.value.length - 1];
      if (last && last.isStreaming) last.isStreaming = false;
      isStreaming.value = false;
      break;
    }
    case "cancelled":
      isStreaming.value = false;
      break;
    case "limit_reached":
      interactionCount.value = msg.interaction_count ?? interactionCount.value;
      interactionLimit.value = msg.interaction_limit ?? interactionLimit.value;
      registerUrl.value = msg.register_url || null;
      limitReached.value = true;
      showRegisterModal.value = true;
      break;
    case "error":
      console.error("Server error:", msg.message);
      isStreaming.value = false;
      break;
  }
}

function scrollToBottom() {
  void nextTick(() => {
    const el = messagesContainer.value;
    if (el) el.scrollTop = el.scrollHeight;
  });
}

function sendMessage() {
  const text = userInput.value.trim();
  if (!text || !canSend.value || !ws || ws.readyState !== WebSocket.OPEN) return;

  messages.value.push({ role: "user", content: text });
  scrollToBottom();
  ws.send(
    JSON.stringify({
      user_message: text,
      current_answers: {},
      current_answers_meta: {},
    }),
  );
  userInput.value = "";

  // Optimistically bump the counter; the server will correct via `limit_reached`.
  interactionCount.value += 1;
  if (interactionCount.value >= interactionLimit.value) {
    limitReached.value = true;
  }
}

async function initialize() {
  setupError.value = null;
  isInitializing.value = true;
  try {
    await loadCatalogAndSession();
    openWebSocket();
  } catch (err: any) {
    console.error(err);
    setupError.value = err?.message || "Unknown error";
  } finally {
    isInitializing.value = false;
  }
}

onMounted(() => {
  void initialize();
});

onBeforeUnmount(() => {
  if (ws && ws.readyState !== WebSocket.CLOSED) {
    ws.close();
  }
});
</script>
