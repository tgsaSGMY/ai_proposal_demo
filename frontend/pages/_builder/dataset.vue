<template>
  <div class="p-4 sm:p-6 md:p-8">
    <header
      class="mb-4 sm:mb-6 flex flex-col sm:flex-row sm:justify-between sm:items-center bg-white p-3 sm:p-4 rounded-lg shadow-sm gap-3 sm:gap-0"
    >
      <h1 class="text-xl sm:text-2xl font-bold text-gray-800 mb-2 sm:mb-0">
        數據生產工作室
      </h1>
      <div class="flex flex-col sm:flex-row flex-wrap items-center gap-2">
        <button
          @click="isBatchModalVisible = true"
          class="btn-primary w-full sm:w-auto flex items-center justify-center gap-1 px-3 py-2"
        >
          🤖 批量 AI 生成
        </button>
        <button
          @click="handleCreateDraft('golden')"
          class="btn-secondary w-full sm:w-auto flex items-center justify-center gap-1 px-3 py-2"
        >
          🏆 新建手動標註
        </button>
        <button
          @click="handleCreateDraft('internal')"
          class="btn-secondary w-full sm:w-auto flex items-center justify-center gap-1 px-3 py-2"
        >
          📝 新建生成企劃
        </button>
      </div>
    </header>

    <DraftPlanList
      :drafts="drafts"
      @select="openEditor"
      @rename="handleRenameDraft"
      @delete="handleDeleteDraft"
      class="mt-4 sm:mt-6"
    />

    <BatchSyntheticModal
      :visible="isBatchModalVisible"
      :all-configs="allConfigs"
      @close="isBatchModalVisible = false"
      @start="handleBatchStart"
    />

    <DraftPlanEditorModal
      v-if="selectedDraft"
      :draft="selectedDraft"
      :all-configs="allConfigs"
      @close="selectedDraft = null"
      @save-to-dataset="handleSaveToFinalDataset"
    />
    <InputPromptModal
      :visible="isInputModalVisible"
      :title="inputModalTitle"
      :message="inputModalMessage"
      :defaultValue="inputModalDefaultValue"
      @submit="handleInputModalSubmit"
      @cancel="handleInputModalCancel"
    />
  </div>
</template>

<script setup>
// SEO 配置
useHead({
  title: "數據生產工作室 - AI 計畫書平台",
  meta: [
    {
      name: "description",
      content:
        "高效的數據生產工作室。支持批量 AI 生成、手動標註和企劃編輯，建立高品質計畫書數據集。",
    },
    {
      name: "keywords",
      content: "數據生產,AI 生成,標註,企劃,工作室",
    },
    {
      property: "og:title",
      content: "數據生產工作室 - AI 計畫書平台",
    },
    {
      property: "og:description",
      content: "高效的數據生產工作室。支持批量 AI 生成、手動標註和企劃編輯。",
    },
  ],
});

// Modal submit/cancel handlers
async function handleInputModalSubmit(value) {
  isInputModalVisible.value = false;
  if (!value || !value.trim()) return;
  if (inputModalMode === "rename" && inputModalDraft) {
    // Rename draft
    if (value === inputModalDraft.name) return;
    try {
      const response = await fetch(
        `${API_BASE_URL}/draft_plans/${inputModalDraft.id}`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ name: value }),
        }
      );
      if (!response.ok)
        throw new Error("重命名失败: " + (await response.text()));
      success(`企划已重命名为 "${value}"`);
      fetchDrafts();
    } catch (e) {
      errorNotification(e.message);
    }
  } else if (inputModalMode === "create" && inputModalDraft) {
    // Create draft
    try {
      const response = await fetch(`${API_BASE_URL}/draft_plans`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: value, mode: inputModalDraft }),
      });
      if (!response.ok)
        throw new Error("创建草稿失败: " + (await response.text()));
      const newDraft = await response.json();
      success(`已创建草稿 "${newDraft.name}"`);
      drafts.value.unshift(newDraft);
    } catch (e) {
      errorNotification(e.message);
    }
  }
  inputModalDraft = null;
}

function handleInputModalCancel() {
  isInputModalVisible.value = false;
  inputModalDraft = null;
}
import { ref, onMounted, onUnmounted, computed } from "vue";
import { supabase } from "~/utils/supabaseClient";
import { usePlanGenerator } from "~/composables/usePlanGenerator";
import { useNotifications } from "~/composables/useNotifications";
import { useConfirm } from "~/composables/useConfirm";
import DraftPlanList from "~/components/DraftPlanList.vue";
import BatchSyntheticModal from "~/components/BatchSyntheticModal.vue";
import DraftPlanEditorModal from "~/components/DraftPlanEditorModal.vue";
import InputPromptModal from "~/components/InputPromptModal.vue";
import { useLoading } from "~/composables/useLoading";
import { getAllCompositeKeys } from "~/utils/dynamicSchema";

// Modal state for renaming and creating drafts
const isInputModalVisible = ref(false);
const inputModalTitle = ref("");
const inputModalMessage = ref("");
const inputModalDefaultValue = ref("");
let inputModalMode = ""; // 'rename' or 'create'
let inputModalDraft = null;

const { success, error: errorNotification } = useNotifications();
const { confirm } = useConfirm();
const config = useRuntimeConfig();
const API_BASE_URL = `${config.public.apiBaseUrl}/api`;
const { show: showLoading, hide: hideLoading } = useLoading();
const { allConfigs, fetchAllConfigs } = usePlanGenerator();

const drafts = ref([]);
const selectedDraft = ref(null);
const isBatchModalVisible = ref(false);
let realtimeChannel = null;

async function handleRenameDraft(draft) {
  inputModalTitle.value = "重命名企划";
  inputModalMessage.value = "请输入新的企划名称:";
  inputModalDefaultValue.value = draft.name;
  inputModalMode = "rename";
  inputModalDraft = draft;
  isInputModalVisible.value = true;
}

async function handleDeleteDraft(draft) {
  const isConfirmed = await confirm({
    title: "確認刪除企劃",
    message: `您確定要刪除企劃 "${draft.name}" 嗎？\n\n⚠️ 此操作無法撤銷。`,
    confirmText: "確認刪除",
    cancelText: "取消",
    confirmColor: "danger",
  });

  if (!isConfirmed) {
    return;
  }

  try {
    const response = await fetch(`${API_BASE_URL}/draft_plans/${draft.id}`, {
      method: "DELETE",
    });
    if (!response.ok) throw new Error("删除失败: " + (await response.text()));
    success(`企划 "${draft.name}" 已被删除。`);
    fetchDrafts();
  } catch (e) {
    errorNotification(e.message);
  }
}

async function fetchDrafts() {
  const { data, error } = await supabase
    .from("draft_plans")
    .select("*")
    .order("created_at", { ascending: false });
  if (error) {
    console.error("Error fetching drafts:", error);
    errorNotification("获取草稿列表失败");
  } else {
    drafts.value = data;
  }
}

onMounted(async () => {
  showLoading("加载中...");
  await fetchAllConfigs(); // Fetch configs for Batch modal
  await fetchDrafts();

  realtimeChannel = supabase
    .channel("public:draft_plans")
    .on(
      "postgres_changes",
      { event: "*", schema: "public", table: "draft_plans" },
      (payload) => {
        fetchDrafts();
      }
    )
    .subscribe();

  hideLoading();
});

onUnmounted(() => {
  if (realtimeChannel) {
    supabase.removeChannel(realtimeChannel);
  }
});

function openEditor(draft) {
  // Make sure user_input and plan_content are valid objects
  if (!draft.user_input) draft.user_input = {};
  if (!draft.plan_content) draft.plan_content = {};
  selectedDraft.value = draft;
}

async function handleCreateDraft(mode) {
  inputModalTitle.value = "新建企划";
  inputModalMessage.value = `请输入新的企划名称 (${
    mode === "golden" ? "手动标注" : "生成企划"
  })：`;
  inputModalDefaultValue.value = "";
  inputModalMode = "create";
  inputModalDraft = mode;
  isInputModalVisible.value = true;
}

async function handleBatchStart(payload) {
  try {
    const payload1 = {
      ...payload,
      dynamic_fields_schema: getAllCompositeKeys(),
    };
    const response = await fetch(
      `${API_BASE_URL}/draft_plans/batch_synthetic`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload1),
      }
    );
    if (response.status !== 202)
      throw new Error("启动批量任务失败: " + (await response.text()));
    success(`已启动 ${payload1.count} 个 AI 生成任务，请关注列表状态更新。`);
  } catch (e) {
    errorNotification(e.message);
  }
}

async function handleSaveToFinalDataset(draftToSave, finalInputs) {
  const {
    id: draftId,
    plan_content,
    user_input,
    grant_id,
    template_id,
    mode,
  } = draftToSave;

  if (!plan_content || Object.keys(plan_content).length === 0) {
    errorNotification("計劃書内容为空，无法保存。");
    return;
  }

  // 顯示確認對話框
  const isConfirmed = await confirm({
    title: "確認保存至最終數據集",
    message: `您確定要保存企劃 "${draftToSave.name}" 至最終數據集嗎？\n\n⚠️ 保存後此數據將自動刪除。\n💾 建議先下載 Word 檔案企劃書。`,
    confirmText: "確認保存",
    cancelText: "取消",
    confirmColor: "primary",
  });

  if (!isConfirmed) {
    return; // 使用者取消操作
  }

  try {
    // 從數據庫獲取最新的 draft 數據，包括 rejected_answer
    showLoading();
    const draftResponse = await fetch(`${API_BASE_URL}/draft_plans/${draftId}`);
    if (!draftResponse.ok) {
      throw new Error("無法從數據庫獲取最新的草稿數據");
    }
    const latestDraft = await draftResponse.json();
    const rejected_answer = latestDraft.rejected_answer || {};

    // Need to find sections based on template_id to iterate
    const grant = allConfigs.value.find((g) => g.id === grant_id);
    const template = grant?.templates.find((t) => t.id === template_id);
    if (!template || !template.sections) {
      throw new Error("無法找到此草稿對應的模板配置。");
    }

    const entries = template.sections
      .map((section) => {
        const content = plan_content[section.id]?.content;
        if (typeof content !== "object" || content === null) return null;

        const entry = {
          source_type:
            mode === "synthetic" || mode == "internal"
              ? "synthetic_data"
              : "golden_samples",
          grant_id: grant_id,
          template_id: template_id,
          section_id: section.id,
          prompt: finalInputs || "",
          final_answer: content,
        };

        if (rejected_answer[section.id]) {
          entry.rejected_answer = rejected_answer[section.id];
        }

        return entry;
      })
      .filter(Boolean);

    if (entries.length === 0) {
      errorNotification("没有有效的章节内容可以保存。");
      return;
    }

    const response = await fetch(`${API_BASE_URL}/datasets`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ entries }),
    });
    if (response.status !== 202)
      throw new Error("保存至数据集失败: " + (await response.text()));

    success(`企划 "${draftToSave.name}" 已成功保存至最终数据集！`);
    await fetch(`${API_BASE_URL}/draft_plans/${draftId}`, {
      method: "DELETE",
    });
    selectedDraft.value = null;
    await fetchDrafts();
    hideLoading();
  } catch (e) {
    errorNotification(`保存失败: ${e.message}`);
    hideLoading();
  }
}
</script>

<style>
.btn-primary {
  @apply bg-indigo-600 text-white font-semibold py-2 px-4 rounded-lg hover:bg-indigo-700 disabled:bg-indigo-300;
}
.btn-secondary {
  @apply bg-gray-200 text-gray-700 font-semibold py-2 px-4 rounded-lg hover:bg-gray-300;
}
</style>
