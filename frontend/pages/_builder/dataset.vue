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
import { ref, onMounted, onUnmounted } from "vue";
import { supabase } from "~/utils/supabaseClient";
import { usePlanGenerator } from "~/composables/usePlanGenerator";
import { useNotifications } from "~/composables/useNotifications";
import DraftPlanList from "~/components/DraftPlanList.vue";
import BatchSyntheticModal from "~/components/BatchSyntheticModal.vue";
import DraftPlanEditorModal from "~/components/DraftPlanEditorModal.vue";

import InputPromptModal from "~/components/InputPromptModal.vue";

// Modal state for renaming and creating drafts
const isInputModalVisible = ref(false);
const inputModalTitle = ref("");
const inputModalMessage = ref("");
const inputModalDefaultValue = ref("");
let inputModalMode = ""; // 'rename' or 'create'
let inputModalDraft = null;

const { success, error: errorNotification } = useNotifications();
const config = useRuntimeConfig();
const API_BASE_URL = `${config.public.apiBaseUrl}/api`;

const { allConfigs, fetchAllConfigs } = usePlanGenerator();

const drafts = ref([]);
const selectedDraft = ref(null);
const isBatchModalVisible = ref(false);
let realtimeChannel = null;

const sectionsForSelectedDraft = computed(() => {
  if (
    !selectedDraft.value ||
    !selectedDraft.value.template_id ||
    !allConfigs.value.length
  ) {
    return [];
  }
  const grant = allConfigs.value.find(
    (g) => g.id === selectedDraft.value.grant_id
  );
  const template = grant?.templates.find(
    (t) => t.id === selectedDraft.value.template_id
  );
  return template?.sections || [];
});

async function handleRenameDraft(draft) {
  inputModalTitle.value = "重命名企划";
  inputModalMessage.value = "请输入新的企划名称:";
  inputModalDefaultValue.value = draft.name;
  inputModalMode = "rename";
  inputModalDraft = draft;
  isInputModalVisible.value = true;
}

async function handleDeleteDraft(draft) {
  if (!confirm(`您确定要删除企划 "${draft.name}" 吗？此操作无法撤销。`)) {
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
  await fetchAllConfigs(); // Fetch configs for Batch modal
  fetchDrafts();

  realtimeChannel = supabase
    .channel("public:draft_plans")
    .on(
      "postgres_changes",
      { event: "*", schema: "public", table: "draft_plans" },
      (payload) => {
        console.log("Realtime change received!", payload);
        fetchDrafts();
      }
    )
    .subscribe();
});

onUnmounted(() => {
  if (realtimeChannel) {
    supabase.removeChannel(realtimeChannel);
  }
});

function openEditor(draft) {
  console.log("hi");
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
    const response = await fetch(
      `${API_BASE_URL}/draft_plans/batch_synthetic`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      }
    );
    if (response.status !== 202)
      throw new Error("启动批量任务失败: " + (await response.text()));
    success(`已启动 ${payload.count} 个 AI 生成任务，请关注列表状态更新。`);
  } catch (e) {
    errorNotification(e.message);
  }
}

async function handleSaveToFinalDataset(draftToSave) {
  const { plan_content, user_input, grant_id, template_id, mode } = draftToSave;

  if (!plan_content || Object.keys(plan_content).length === 0) {
    errorNotification("計劃書内容为空，无法保存。");
    return;
  }

  try {
    // Need to find sections based on template_id to iterate
    const grant = allConfigs.value.find((g) => g.id === grant_id);
    const template = grant?.templates.find((t) => t.id === template_id);
    if (!template || !template.sections) {
      throw new Error("无法找到此草稿对应的模板配置。");
    }

    const entries = template.sections
      .map((section) => {
        const content = plan_content[section.id]?.content;
        if (typeof content !== "object" || content === null) return null;
        return {
          source_type:
            mode === "synthetic" || mode == "internal"
              ? "synthetic_data"
              : "golden_samples",
          grant_id: grant_id,
          template_id: template_id,
          section_id: section.id,
          prompt: user_input?.main_idea || "",
          final_answer: content,
        };
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
    await fetch(`${API_BASE_URL}/draft_plans/${draftToSave.id}`, {
      method: "DELETE",
    });
    selectedDraft.value = null;
    await fetchDrafts();
  } catch (e) {
    errorNotification(`保存失败: ${e.message}`);
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
