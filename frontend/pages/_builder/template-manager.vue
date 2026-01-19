<template>
  <ClientOnly>
    <div class="p-4 md:p-8 space-y-6">
      <header
        class="bg-white rounded-2xl shadow-sm p-5 sm:p-6 flex flex-col gap-3"
      >
        <div>
          <p
            class="text-xs font-semibold uppercase tracking-[0.3em] text-rose-400"
          >
            Builder / Template Manager
          </p>
          <h1 class="text-2xl font-bold text-slate-900">主題與模板管理</h1>
        </div>
        <p class="text-sm text-slate-500">
          在此新增或調整補助主題 (Grant)
          以及底下可用的計畫模板。僅支援新增與更新，避免誤刪正式環境資料。
        </p>
      </header>

      <GrantListSection
        :grants="grants"
        @new="openGrantModal('create')"
        @edit="(grant) => startGrantEdit(grant)"
        @refresh="loadInitialData"
      />

      <TemplateListSection
        v-model:template-filter="templateFilter"
        :templates="templates"
        :grant-options="grantOptions"
        :grant-name-map="grantNameMap"
        @new="openTemplateModal('create')"
        @edit="(template) => startTemplateEdit(template)"
      />

      <GrantFormModal
        v-model:grant-form="grantForm"
        :is-visible="showGrantModal"
        :grant-form-mode="grantFormMode"
        :saving="grantSaving"
        @submit="handleGrantSubmit"
        @cancel="closeGrantModal"
      />

      <TemplateFormModal
        v-model:template-form="templateForm"
        :is-visible="showTemplateModal"
        :grant-options="grantOptions"
        :template-form-mode="templateFormMode"
        :template-saving="templateSaving"
        @submit="handleTemplateSubmit"
        @cancel="closeTemplateModal"
      />
    </div>
  </ClientOnly>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import GrantListSection from "~/components/template-manager/grant-manager.vue";
import TemplateListSection from "~/components/template-manager/template-manager.vue";
import GrantFormModal from "~/components/template-manager/GrantFormModal.vue";
import TemplateFormModal from "~/components/template-manager/TemplateFormModal.vue";
import { supabase } from "~/utils/supabaseClient";
import { useNotifications } from "~/composables/useNotifications";
import { useInternalCheck } from "~/composables/useInternalCheck";

definePageMeta({
  middleware: "auth",
});

useHead({
  title: "主題與模板管理- AI補助引擎",
  meta: [
    {
      name: "description",
      content: "管理補助主題與模板，用於控制前臺可選擇的方案。",
    },
  ],
});

interface GrantRecord {
  id: string;
  name: string;
  [key: string]: any;
}

interface TemplateRecord {
  id: string;
  grant_id: string;
  name: string;
  subtitle?: string | null;
  description?: string | null;
  logo_storage_path?: string | null;
  iconBg?: string | null;
  isOpen?: boolean | null;
  [key: string]: any;
}

interface GrantFormState {
  id: string;
  name: string;
}

interface TemplateFormState {
  id: string;
  grant_id: string;
  name: string;
  subtitle: string;
  description: string;
  logo_storage_path: string;
  iconBg: string;
  isOpen: boolean;
}

const grants = ref<GrantRecord[]>([]);
const templates = ref<TemplateRecord[]>([]);
const templateFilter = ref("");
const grantFormMode = ref<"create" | "edit">("create");
const templateFormMode = ref<"create" | "edit">("create");
const grantSaving = ref(false);
const templateSaving = ref(false);
const grantEditingId = ref<string | null>(null);
const templateEditingKeys = ref<{ grant_id: string; id: string } | null>(null);
const showGrantModal = ref(false);
const showTemplateModal = ref(false);

const grantForm = ref<GrantFormState>({
  id: "",
  name: "",
});

const templateForm = ref<TemplateFormState>({
  id: "",
  grant_id: "",
  name: "",
  subtitle: "",
  description: "",
  logo_storage_path: "",
  iconBg: "#F8FAFC",
  isOpen: true,
});

const config = useRuntimeConfig();
const API_BASE_URL = `${config.public.apiBaseUrl}/api`;
const TEMPLATE_MANAGER_API = `${API_BASE_URL}/template-manager`;

const { success, error: notifyError } = useNotifications();
const { checkIsInternal } = useInternalCheck();

const grantOptions = computed(() =>
  grants.value.map((grant) => ({ label: grant.name, value: grant.id }))
);

const grantNameMap = computed(() => {
  const map = new Map<string, string>();
  grants.value.forEach((grant) => map.set(grant.id, grant.name));
  return map;
});

function generateLogoStoragePath(templateId: string) {
  const normalized = templateId.trim();
  return normalized ? `logos/${normalized}_logo.png` : "";
}

watch(
  () => templateForm.value.id,
  (newId = "") => {
    templateForm.value.logo_storage_path = generateLogoStoragePath(newId);
  }
);

async function fetchWithAuth(url: string, options: RequestInit = {}) {
  const {
    data: { session },
  } = await supabase.auth.getSession();
  if (!session?.access_token) {
    throw new Error("請先登入");
  }

  const headers = new Headers(options.headers || {});
  headers.set("Authorization", `Bearer ${session.access_token}`);
  if (options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  return fetch(url, {
    ...options,
    headers,
  });
}

async function fetchJsonWithAuth<T>(
  url: string,
  options: RequestInit = {}
): Promise<T> {
  const response = await fetchWithAuth(url, options);
  if (!response.ok) {
    const detail = await response.json().catch(() => ({}));
    throw new Error(detail.detail || "操作失敗");
  }
  return response.json();
}

async function loadInitialData() {
  try {
    const [grantData, templateData] = await Promise.all([
      fetchJsonWithAuth<GrantRecord[]>(`${TEMPLATE_MANAGER_API}/grants`),
      fetchJsonWithAuth<TemplateRecord[]>(`${TEMPLATE_MANAGER_API}/templates`),
    ]);
    grants.value = grantData;
    templates.value = templateData;
  } catch (error: any) {
    notifyError(error?.message || "無法載入資料");
  }
}

function openGrantModal(mode: "create" | "edit") {
  grantFormMode.value = mode;
  if (mode === "create") {
    resetGrantForm();
  }
  showGrantModal.value = true;
}

function closeGrantModal() {
  showGrantModal.value = false;
  resetGrantForm();
}

function openTemplateModal(mode: "create" | "edit") {
  templateFormMode.value = mode;
  if (mode === "create") {
    resetTemplateForm();
  }
  showTemplateModal.value = true;
}

function closeTemplateModal() {
  showTemplateModal.value = false;
  resetTemplateForm();
}

function resetGrantForm() {
  grantForm.value = {
    id: "",
    name: "",
  };
  grantFormMode.value = "create";
  grantEditingId.value = null;
}

function startGrantEdit(grant: GrantRecord) {
  grantFormMode.value = "edit";
  grantEditingId.value = grant.id;
  grantForm.value = {
    id: grant.id,
    name: grant.name,
  };
  openGrantModal("edit");
}

async function handleGrantSubmit() {
  if (!grantForm.value.id.trim() || !grantForm.value.name.trim()) {
    notifyError("請完整填寫 Grant ID 與名稱");
    return;
  }

  grantSaving.value = true;
  try {
    const payload = {
      id: grantForm.value.id.trim(),
      name: grantForm.value.name.trim(),
    };

    if (grantFormMode.value === "create") {
      await fetchJsonWithAuth(`${TEMPLATE_MANAGER_API}/grants`, {
        method: "POST",
        body: JSON.stringify(payload),
      });
      success("已新增主題");
    } else if (grantEditingId.value) {
      await fetchJsonWithAuth(
        `${TEMPLATE_MANAGER_API}/grants/${grantEditingId.value}`,
        {
          method: "PUT",
          body: JSON.stringify({
            name: payload.name,
            id: payload.id !== grantEditingId.value ? payload.id : undefined,
          }),
        }
      );
      success("主題已更新");
    }

    await loadInitialData();
    closeGrantModal();
  } catch (error: any) {
    notifyError(error?.message || "操作失敗");
  } finally {
    grantSaving.value = false;
  }
}

function resetTemplateForm() {
  templateFormMode.value = "create";
  templateEditingKeys.value = null;
  templateForm.value = {
    id: "",
    grant_id: "",
    name: "",
    subtitle: "",
    description: "",
    logo_storage_path: "",
    iconBg: "#F8FAFC",
    isOpen: true,
  };
}

function startTemplateEdit(template: TemplateRecord) {
  templateFormMode.value = "edit";
  templateEditingKeys.value = { grant_id: template.grant_id, id: template.id };
  templateForm.value = {
    id: template.id,
    grant_id: template.grant_id,
    name: template.name,
    subtitle: template.subtitle || "",
    description: template.description || "",
    logo_storage_path: template.logo_storage_path || "",
    iconBg: template.iconBg || "#F8FAFC",
    isOpen: template.isOpen !== false,
  };
  openTemplateModal("edit");
}

async function handleTemplateSubmit() {
  if (
    !templateForm.value.grant_id ||
    !templateForm.value.id.trim() ||
    !templateForm.value.name.trim()
  ) {
    notifyError("請至少填寫主題、Template ID 與名稱");
    return;
  }

  templateSaving.value = true;
  const derivedLogoPath = generateLogoStoragePath(templateForm.value.id || "");
  const payload = {
    id: templateForm.value.id.trim(),
    grant_id: templateForm.value.grant_id,
    name: templateForm.value.name.trim(),
    subtitle: templateForm.value.subtitle?.trim() || null,
    description: templateForm.value.description?.trim() || null,
    logo_storage_path: derivedLogoPath || null,
    iconBg: templateForm.value.iconBg?.trim() || null,
    isOpen: templateForm.value.isOpen,
  };

  try {
    if (templateFormMode.value === "create") {
      await fetchJsonWithAuth(`${TEMPLATE_MANAGER_API}/templates`, {
        method: "POST",
        body: JSON.stringify(payload),
      });
      success("已新增模板");
    } else if (templateEditingKeys.value) {
      await fetchJsonWithAuth(
        `${TEMPLATE_MANAGER_API}/templates/${templateEditingKeys.value.grant_id}/${templateEditingKeys.value.id}`,
        {
          method: "PUT",
          body: JSON.stringify({
            grant_id: payload.grant_id,
            name: payload.name,
            subtitle: payload.subtitle,
            description: payload.description,
            logo_storage_path: payload.logo_storage_path,
            iconBg: payload.iconBg,
            isOpen: payload.isOpen,
          }),
        }
      );
      success("模板已更新");
    }

    await loadInitialData();
    closeTemplateModal();
  } catch (error: any) {
    notifyError(error?.message || "操作失敗");
  } finally {
    templateSaving.value = false;
  }
}

onMounted(async () => {
  const isInternal = await checkIsInternal();
  if (!isInternal) {
    window.location.href = "/";
    return;
  }
  await loadInitialData();
});
</script>
