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
        @sections="(template) => openSectionEditor(template)"
        @word-editor="(template) => openWordEditor(template)"
        @name-config="(template) => openNameRecommendModal(template)"
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
        ref="templateFormModalRef"
        v-model:template-form="templateForm"
        :is-visible="showTemplateModal"
        :grant-options="grantOptions"
        :template-form-mode="templateFormMode"
        :template-saving="templateSaving"
        @submit="handleTemplateSubmit"
        @cancel="closeTemplateModal"
      />

      <SectionEditorModal
        :is-visible="showSectionModal"
        :template="sectionModalTemplate"
        :sections="sectionRecords"
        :loading="sectionLoading"
        :saving="sectionSaving"
        @close="closeSectionModal"
        @create="handleSectionCreate"
        @update="handleSectionUpdate"
        @delete="handleSectionDelete"
        @reorder="handleSectionReorder"
      />

      <WordEditorForm
        :is-visible="showWordEditorModal"
        :template="wordEditorTemplate"
        :sections="wordEditorSections"
        :saving="wordEditorSaving"
        @close="closeWordEditorModal"
        @save="handleWordEditorSave"
      />

      <NameRecommendForm
        :is-visible="showNameRecommendModal"
        :template="nameRecommendTemplate"
        :saving="nameRecommendSaving"
        @close="closeNameRecommendModal"
        @save="handleNameRecommendSave"
      />
    </div>
  </ClientOnly>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import GrantListSection from "~/components/template-manager/grant-manager.vue";
import TemplateListSection from "~/components/template-manager/template-manager.vue";
import GrantFormModal from "~/components/template-manager/GrantFormModal.vue";
import TemplateFormModal from "~/components/template-manager/TemplateFormModal.vue";
import SectionEditorModal from "~/components/template-manager/SectionEditorModal.vue";
import WordEditorForm from "~/components/template-manager/WordEditorForm.vue";
import NameRecommendForm from "~/components/template-manager/NameRecommendForm.vue";
import { supabase } from "~/utils/supabaseClient";
import { useNotifications } from "~/composables/useNotifications";
import { useInternalCheck } from "~/composables/useInternalCheck";
import type {
  WordExportConfigEntry,
  WordExportTemplateConfig,
} from "~/types/wordExport";
import type { NameRecommendConfig } from "~/types/nameRecommend";

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
  word_export_config?: WordExportConfigEntry[] | null;
  name_recommend_config?: NameRecommendConfig | null;
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

interface SectionRecord {
  id: string;
  template_id: string;
  grant_id: string;
  name: string;
  order?: number | null;
  json_schema?: Record<string, any> | null;
  [key: string]: any;
}

interface SectionMutationPayload {
  id: string;
  name: string;
  order: number;
  json_schema: Record<string, any> | null;
  originalId?: string | null;
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
const templateFormModalRef = ref<any>(null);
const showSectionModal = ref(false);
const sectionModalTemplate = ref<TemplateRecord | null>(null);
const sectionRecords = ref<SectionRecord[]>([]);
const sectionLoading = ref(false);
const sectionSaving = ref(false);
const showWordEditorModal = ref(false);
const wordEditorTemplate = ref<TemplateRecord | null>(null);
const wordEditorSections = ref<SectionRecord[]>([]);
const wordEditorSaving = ref(false);
const showNameRecommendModal = ref(false);
const nameRecommendTemplate = ref<TemplateRecord | null>(null);
const nameRecommendSaving = ref(false);

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
  grants.value.map((grant) => ({ label: grant.name, value: grant.id })),
);

const grantNameMap = computed(() => {
  const map = new Map<string, string>();
  grants.value.forEach((grant) => map.set(grant.id, grant.name));
  return map;
});

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
  options: RequestInit = {},
): Promise<T> {
  const response = await fetchWithAuth(url, options);
  if (!response.ok) {
    const detail = await response.json().catch(() => ({}));
    throw new Error(detail.detail || "操作失敗");
  }
  return response.json();
}

async function fetchSections(grantId: string, templateId: string) {
  const params = new URLSearchParams({
    grant_id: grantId,
    template_id: templateId,
  });
  return fetchJsonWithAuth<SectionRecord[]>(
    `${TEMPLATE_MANAGER_API}/sections?${params.toString()}`,
  );
}

async function fetchWithFormDataAuth(
  url: string,
  formData: FormData,
  options: RequestInit = {},
) {
  const {
    data: { session },
  } = await supabase.auth.getSession();
  if (!session?.access_token) {
    throw new Error("請先登入");
  }

  const headers = new Headers(options.headers || {});
  headers.set("Authorization", `Bearer ${session.access_token}`);
  // 不設置 Content-Type，讓瀏覽器自動設置 multipart/form-data

  const response = await fetch(url, {
    ...options,
    method: options.method || "POST",
    headers,
    body: formData,
  });

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

  if (!/^[a-zA-Z0-9_]+$/.test(grantForm.value.id.trim())) {
    notifyError("Grant ID 只能包含英文字母、數字和底線");
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
        },
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

  if (!/^[a-zA-Z0-9_]+$/.test(templateForm.value.id.trim())) {
    notifyError("Template ID 只能包含英文字母、數字和底線");
    return;
  }

  templateSaving.value = true;
  try {
    const formData = new FormData();

    // 添加基本字段
    formData.append("id", templateForm.value.id.trim());
    formData.append("grant_id", templateForm.value.grant_id);
    formData.append("name", templateForm.value.name.trim());
    formData.append("subtitle", templateForm.value.subtitle?.trim() || "");
    formData.append(
      "description",
      templateForm.value.description?.trim() || "",
    );
    formData.append("iconBg", templateForm.value.iconBg?.trim() || "#F8FAFC");
    formData.append("isOpen", templateForm.value.isOpen ? "true" : "false");

    // 如果有选择新文件，添加文件
    const logoFile = templateFormModalRef.value?.getSelectedLogoFile();
    if (logoFile) {
      formData.append("logo_file", logoFile);
    }

    if (templateFormMode.value === "create") {
      await fetchWithFormDataAuth(
        `${TEMPLATE_MANAGER_API}/templates/upload`,
        formData,
      );
      success("已新增模板");
    } else if (templateEditingKeys.value) {
      formData.append("template_id", templateEditingKeys.value.id);
      await fetchWithFormDataAuth(
        `${TEMPLATE_MANAGER_API}/templates/${templateEditingKeys.value.grant_id}/${templateEditingKeys.value.id}/upload`,
        formData,
        { method: "PUT" },
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

async function openSectionEditor(template: TemplateRecord) {
  sectionModalTemplate.value = template;
  sectionRecords.value = [];
  showSectionModal.value = true;
  await fetchSectionsForTemplate(template);
}

function closeSectionModal() {
  showSectionModal.value = false;
  sectionModalTemplate.value = null;
  sectionRecords.value = [];
}

async function fetchSectionsForTemplate(template: TemplateRecord) {
  sectionLoading.value = true;
  try {
    sectionRecords.value = await fetchSections(template.grant_id, template.id);
  } catch (error: any) {
    notifyError(error?.message || "無法載入章節");
  } finally {
    sectionLoading.value = false;
  }
}

async function handleSectionCreate(payload: SectionMutationPayload) {
  const template = sectionModalTemplate.value;
  if (!template) {
    notifyError("請先選擇模板");
    return;
  }

  sectionSaving.value = true;
  try {
    const { originalId, ...sectionPayload } = payload;
    await fetchJsonWithAuth(`${TEMPLATE_MANAGER_API}/sections`, {
      method: "POST",
      body: JSON.stringify({
        ...sectionPayload,
        grant_id: template.grant_id,
        template_id: template.id,
      }),
    });
    success("章節已新增");
    await fetchSectionsForTemplate(template);
  } catch (error: any) {
    notifyError(error?.message || "章節新增失敗");
  } finally {
    sectionSaving.value = false;
  }
}

async function handleSectionUpdate(payload: SectionMutationPayload) {
  const template = sectionModalTemplate.value;
  if (!template) {
    notifyError("請先選擇模板");
    return;
  }

  const targetId = payload.originalId || payload.id;
  sectionSaving.value = true;
  try {
    const { originalId, ...sectionPayload } = payload;
    await fetchJsonWithAuth(
      `${TEMPLATE_MANAGER_API}/sections/${template.grant_id}/${template.id}/${targetId}`,
      {
        method: "PUT",
        body: JSON.stringify(sectionPayload),
      },
    );
    success("章節已更新");
    await fetchSectionsForTemplate(template);
  } catch (error: any) {
    notifyError(error?.message || "章節更新失敗");
  } finally {
    sectionSaving.value = false;
  }
}

async function handleSectionDelete(section: SectionRecord) {
  sectionSaving.value = true;
  try {
    await fetchJsonWithAuth(
      `${TEMPLATE_MANAGER_API}/sections/${section.grant_id}/${section.template_id}/${section.id}`,
      { method: "DELETE" },
    );
    success("章節已刪除");
    if (sectionModalTemplate.value) {
      await fetchSectionsForTemplate(sectionModalTemplate.value);
    }
  } catch (error: any) {
    notifyError(error?.message || "章節刪除失敗");
  } finally {
    sectionSaving.value = false;
  }
}

async function handleSectionReorder(changedSections: SectionRecord[]) {
  const template = sectionModalTemplate.value;
  if (!template || !changedSections?.length) {
    return;
  }

  sectionSaving.value = true;
  try {
    for (const section of changedSections) {
      await fetchJsonWithAuth(
        `${TEMPLATE_MANAGER_API}/sections/${template.grant_id}/${template.id}/${section.id}`,
        {
          method: "PUT",
          body: JSON.stringify({
            id: section.id,
            name: section.name,
            order: section.order ?? 0,
            json_schema: section.json_schema ?? null,
          }),
        },
      );
    }
    success("章節順序已更新");
    await fetchSectionsForTemplate(template);
  } catch (error: any) {
    notifyError(error?.message || "章節排序更新失敗");
  } finally {
    sectionSaving.value = false;
  }
}

async function openWordEditor(template: TemplateRecord) {
  try {
    wordEditorTemplate.value = template;
    wordEditorSections.value = await fetchSections(
      template.grant_id,
      template.id,
    );
    showWordEditorModal.value = true;
  } catch (error: any) {
    console.error("Failed to load sections for word editor", error);
    notifyError(error?.message || "無法載入文檔設定");
  }
}

function closeWordEditorModal() {
  showWordEditorModal.value = false;
  wordEditorTemplate.value = null;
  wordEditorSections.value = [];
}

async function handleWordEditorSave(config: WordExportTemplateConfig) {
  const template = wordEditorTemplate.value;
  if (!template) {
    notifyError("未選擇模板");
    return;
  }

  wordEditorSaving.value = true;
  try {
    const {
      data: { user },
    } = await supabase.auth.getUser();

    const clonedConfig = JSON.parse(JSON.stringify(config));
    const newEntry: WordExportConfigEntry = {
      id: createWordConfigVersionId(),
      createdAt: new Date().toISOString(),
      createdBy: user?.email || user?.id || "internal",
      config: clonedConfig,
    };

    const nextList = [...(template.word_export_config ?? []), newEntry];

    await fetchJsonWithAuth(
      `${TEMPLATE_MANAGER_API}/templates/${template.grant_id}/${template.id}`,
      {
        method: "PUT",
        body: JSON.stringify({ word_export_config: nextList }),
      },
    );

    // 先刷新數據，再關閉模態框和顯示提示
    await loadInitialData();
    success("Word 文檔設定已更新");
    closeWordEditorModal();
  } catch (error: any) {
    console.error("Failed to save word export config", error);
    notifyError(error?.message || "儲存文檔設定失敗");
  } finally {
    wordEditorSaving.value = false;
  }
}

function openNameRecommendModal(template: TemplateRecord) {
  nameRecommendTemplate.value = template;
  showNameRecommendModal.value = true;
}

function closeNameRecommendModal() {
  showNameRecommendModal.value = false;
  nameRecommendTemplate.value = null;
}

async function handleNameRecommendSave(config: NameRecommendConfig) {
  const template = nameRecommendTemplate.value;
  if (!template) {
    notifyError("未選擇模板");
    return;
  }

  nameRecommendSaving.value = true;
  try {
    const shouldClear = !config.traits && config.examples.length === 0;
    await fetchJsonWithAuth(
      `${TEMPLATE_MANAGER_API}/templates/${template.grant_id}/${template.id}`,
      {
        method: "PUT",
        body: JSON.stringify({
          name_recommend_config: shouldClear ? null : config,
        }),
      },
    );
    success("推薦名稱設定已更新");
    await loadInitialData();
    closeNameRecommendModal();
  } catch (error: any) {
    notifyError(error?.message || "儲存推薦設定失敗");
  } finally {
    nameRecommendSaving.value = false;
  }
}

function createWordConfigVersionId() {
  if (
    typeof crypto !== "undefined" &&
    typeof crypto.randomUUID === "function"
  ) {
    return crypto.randomUUID();
  }
  return `wordcfg_${Date.now()}_${Math.random().toString(16).slice(2)}`;
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
