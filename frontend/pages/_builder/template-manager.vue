<!-- 内部使用的主題與模板管理界面，提供對補助主題（Grant）和計畫模板的增刪改查功能，以及相關設定的管理。用於控制前臺用戶在選擇方案時可見的主題和模板選項。 -->
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
        :loading="templateSaving"
        @new="openTemplateModal('create')"
        @edit="(template) => startTemplateEdit(template)"
        @sections="(template) => openSectionEditor(template)"
        @word-editor="(template) => openWordEditor(template)"
        @name-config="(template) => openNameRecommendModal(template)"
        @reorder="handleTemplateReorder"
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
        @delete-version="handleWordEditorDeleteVersion"
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
import { authenticatedFetch } from "~/composables/useAppAuth";
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
  title: "主題與模板管理- TGSA 補助引擎",
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
  order?: number | null;
  name: string;
  requires_paid_plan?: boolean | null;
  submission_deadline?: string | null;
  subsidy_amount?: string | null;
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
  requires_paid_plan: boolean;
  submission_deadline: string;
  subsidy_amount: string;
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

interface TemplateReorderPayload {
  id: string;
  grant_id: string;
  order: number;
}

// 主畫面資料與 UI 狀態
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

// Grant 表單狀態
const grantForm = ref<GrantFormState>({
  id: "",
  name: "",
});

// Template 表單狀態
const templateForm = ref<TemplateFormState>({
  id: "",
  grant_id: "",
  name: "",
  requires_paid_plan: true,
  submission_deadline: "",
  subsidy_amount: "",
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

// 給下拉選單使用的 Grant 清單
const grantOptions = computed(() =>
  grants.value.map((grant) => ({ label: grant.name, value: grant.id })),
);

// 提供模板列表快速查詢 Grant 名稱
const grantNameMap = computed(() => {
  const map = new Map<string, string>();
  grants.value.forEach((grant) => map.set(grant.id, grant.name));
  return map;
});

// 通用授權請求包裝：有 body 時補上 JSON Content-Type
async function fetchWithAuth(url: string, options: RequestInit = {}) {
  const headers = new Headers(options.headers || {});
  if (options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  return authenticatedFetch(url, {
    ...options,
    headers,
  });
}

// 通用 JSON API 請求：統一錯誤處理與型別回傳
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

// 載入指定 Grant + Template 的章節列表
async function fetchSections(grantId: string, templateId: string) {
  const params = new URLSearchParams({
    grant_id: grantId,
    template_id: templateId,
  });
  return fetchJsonWithAuth<SectionRecord[]>(
    `${TEMPLATE_MANAGER_API}/sections?${params.toString()}`,
  );
}

// FormData 專用請求（支援檔案上傳）
async function fetchWithFormDataAuth(
  url: string,
  formData: FormData,
  options: RequestInit = {},
) {
  const response = await authenticatedFetch(url, {
    ...options,
    method: options.method || "POST",
    body: formData,
  });

  if (!response.ok) {
    const detail = await response.json().catch(() => ({}));
    throw new Error(detail.detail || "操作失敗");
  }
  return response.json();
}

// 首頁初始化：一次拉取 grants 與 templates
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

// 開啟 Grant 表單；create 模式會先清空
function openGrantModal(mode: "create" | "edit") {
  grantFormMode.value = mode;
  if (mode === "create") {
    resetGrantForm();
  }
  showGrantModal.value = true;
}

// 關閉 Grant 表單並重置狀態
function closeGrantModal() {
  showGrantModal.value = false;
  resetGrantForm();
}

// 開啟 Template 表單；create 模式會先清空
function openTemplateModal(mode: "create" | "edit") {
  templateFormMode.value = mode;
  if (mode === "create") {
    resetTemplateForm();
  }
  showTemplateModal.value = true;
}

// 關閉 Template 表單並重置狀態
function closeTemplateModal() {
  showTemplateModal.value = false;
  resetTemplateForm();
}

// 重置 Grant 表單與編輯狀態
function resetGrantForm() {
  grantForm.value = {
    id: "",
    name: "",
  };
  grantFormMode.value = "create";
  grantEditingId.value = null;
}

// 將指定 Grant 資料帶入編輯表單
function startGrantEdit(grant: GrantRecord) {
  grantFormMode.value = "edit";
  grantEditingId.value = grant.id;
  grantForm.value = {
    id: grant.id,
    name: grant.name,
  };
  openGrantModal("edit");
}

// 送出 Grant 表單：create / update 共用入口
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

// 重置 Template 表單與編輯狀態
function resetTemplateForm() {
  templateFormMode.value = "create";
  templateEditingKeys.value = null;
  templateForm.value = {
    id: "",
    grant_id: "",
    name: "",
    requires_paid_plan: true,
    submission_deadline: "",
    subsidy_amount: "",
    subtitle: "",
    description: "",
    logo_storage_path: "",
    iconBg: "#F8FAFC",
    isOpen: true,
  };
}

// 將指定 Template 資料帶入編輯表單
function startTemplateEdit(template: TemplateRecord) {
  templateFormMode.value = "edit";
  templateEditingKeys.value = { grant_id: template.grant_id, id: template.id };
  templateForm.value = {
    id: template.id,
    grant_id: template.grant_id,
    name: template.name,
    requires_paid_plan: template.requires_paid_plan !== false,
    submission_deadline: template.submission_deadline || "",
    subsidy_amount: template.subsidy_amount || "",
    subtitle: template.subtitle || "",
    description: template.description || "",
    logo_storage_path: template.logo_storage_path || "",
    iconBg: template.iconBg || "#F8FAFC",
    isOpen: template.isOpen !== false,
  };
  openTemplateModal("edit");
}

// 送出 Template 表單：含文字欄位與可選 logo 檔案上傳
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
    formData.append(
      "requires_paid_plan",
      templateForm.value.requires_paid_plan ? "true" : "false",
    );
    formData.append(
      "submission_deadline",
      templateForm.value.submission_deadline?.trim() || "",
    );
    formData.append(
      "subsidy_amount",
      templateForm.value.subsidy_amount?.trim() || "",
    );
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

// 更新模板排序：只送出實際有變動的項目，避免不必要 API 請求
async function handleTemplateReorder(
  changedTemplates: TemplateReorderPayload[],
) {
  if (!changedTemplates?.length) {
    return;
  }

  const currentOrderMap = new Map<string, number>();
  templates.value.forEach((template) => {
    const key = `${template.grant_id}::${template.id}`;
    currentOrderMap.set(key, Number(template.order ?? 0));
  });

  const templatesToUpdate = changedTemplates.filter((template) => {
    const key = `${template.grant_id}::${template.id}`;
    return currentOrderMap.get(key) !== Number(template.order ?? 0);
  });

  if (!templatesToUpdate.length) {
    return;
  }

  templateSaving.value = true;
  try {
    await Promise.all(
      templatesToUpdate.map((template) =>
        fetchJsonWithAuth(
          `${TEMPLATE_MANAGER_API}/templates/${template.grant_id}/${template.id}`,
          {
            method: "PUT",
            body: JSON.stringify({ order: template.order }),
          },
        ),
      ),
    );

    const updatedOrderMap = new Map(
      templatesToUpdate.map((template) => [
        `${template.grant_id}::${template.id}`,
        template.order,
      ]),
    );
    templates.value = templates.value.map((template) => {
      const key = `${template.grant_id}::${template.id}`;
      const nextOrder = updatedOrderMap.get(key);
      if (nextOrder === undefined) {
        return template;
      }
      return {
        ...template,
        order: nextOrder,
      };
    });

    success("模板順序已更新");
  } catch (error: any) {
    notifyError(error?.message || "模板排序更新失敗");
  } finally {
    templateSaving.value = false;
  }
}

// 開啟章節編輯器並載入該模板章節
async function openSectionEditor(template: TemplateRecord) {
  sectionModalTemplate.value = template;
  sectionRecords.value = [];
  showSectionModal.value = true;
  await fetchSectionsForTemplate(template);
}

// 關閉章節編輯器並清除暫存狀態
function closeSectionModal() {
  showSectionModal.value = false;
  sectionModalTemplate.value = null;
  sectionRecords.value = [];
}

// 重新抓取當前模板章節
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

// 新增章節
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

// 更新章節；若有改 id，會使用 originalId 指向舊紀錄
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

// 刪除章節並刷新列表
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

// 章節排序更新
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

// 開啟 Word 設定編輯器並預載章節資料
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

// 關閉 Word 設定編輯器並清空暫存
function closeWordEditorModal() {
  showWordEditorModal.value = false;
  wordEditorTemplate.value = null;
  wordEditorSections.value = [];
}

// 儲存 Word 匯出設定：以版本快照方式 append 到設定歷史
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

    // 收集所有 section 的當前版本號
    const sectionVersions: Record<string, number> = {};
    for (const section of wordEditorSections.value) {
      sectionVersions[section.id] = section.current_version || 1;
    }

    const newEntry: WordExportConfigEntry = {
      id: createWordConfigVersionId(),
      createdAt: new Date().toISOString(),
      createdBy: user?.email || user?.id || "internal",
      config: clonedConfig,
      section_versions: sectionVersions,
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

// 刪除 Word 匯出設定歷史版本
async function handleWordEditorDeleteVersion(versionId: string) {
  const template = wordEditorTemplate.value;
  if (!template || !template.word_export_config) return;

  wordEditorSaving.value = true;
  try {
    const nextList = template.word_export_config.filter(v => v.id !== versionId);

    await fetchJsonWithAuth(
      `${TEMPLATE_MANAGER_API}/templates/${template.grant_id}/${template.id}`,
      {
        method: "PUT",
        body: JSON.stringify({ word_export_config: nextList }),
      },
    );

    await loadInitialData();
    
    // 更新本地狀態以即時反應 UI
    if (wordEditorTemplate.value) {
       wordEditorTemplate.value.word_export_config = nextList;
    }
    
    success("歷史版本已刪除");
  } catch (error: any) {
    notifyError(error?.message || "刪除歷史版本失敗");
  } finally {
    wordEditorSaving.value = false;
  }
}

// 開啟推薦名稱設定 modal
function openNameRecommendModal(template: TemplateRecord) {
  nameRecommendTemplate.value = template;
  showNameRecommendModal.value = true;
}

// 關閉推薦名稱設定 modal
function closeNameRecommendModal() {
  showNameRecommendModal.value = false;
  nameRecommendTemplate.value = null;
}

// 儲存推薦名稱設定；若內容為空則清除後端設定
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

// 建立 Word 設定版本 ID（優先使用原生 UUID）
function createWordConfigVersionId() {
  if (
    typeof crypto !== "undefined" &&
    typeof crypto.randomUUID === "function"
  ) {
    return crypto.randomUUID();
  }
  return `wordcfg_${Date.now()}_${Math.random().toString(16).slice(2)}`;
}

// 僅內部使用者可進入本頁，通過後才載入初始資料
onMounted(async () => {
  const isInternal = await checkIsInternal();
  if (!isInternal) {
    window.location.href = "/";
    return;
  }
  await loadInitialData();
});
</script>
