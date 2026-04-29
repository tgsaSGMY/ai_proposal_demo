<!-- 内部人員使用的數據生產工作室，支持批量 AI 生成、手動標註和計畫編輯，建立高品質計畫書數據集。 -->
<template>
  <ClientOnly>
    <div class="p-4 sm:p-6 md:p-8">
      <header
        class="mb-4 sm:mb-6 flex flex-col sm:flex-row sm:justify-between sm:items-center bg-white p-3 sm:p-4 rounded-lg shadow-sm gap-3 sm:gap-0"
      >
        <h1 class="text-xl sm:text-2xl font-bold text-gray-800 mb-2 sm:mb-0">
          模擬數據生產工作室
          <p class="text-sm sm:text-md text-gray-400 mb-2 sm:mb-0">
            當某類計畫書生成效果不好時，可以使用此頁面生成優秀的計畫書讓AI學習。
          </p>
        </h1>

        <div class="flex flex-col sm:flex-row flex-wrap items-center gap-2">
          <button
            @click="isBatchModalVisible = true"
            class="btn-primary w-full sm:w-auto flex items-center justify-center gap-1 px-3 py-2"
          >
            🤖 AI 隨機生成想法
          </button>
          <button
            @click="handleCreateDraft('golden')"
            class="btn-secondary w-full sm:w-auto flex items-center justify-center gap-1 px-3 py-2"
          >
            🏆 導入範例計畫書
          </button>
          <!-- <button
            @click="handleCreateDraft('internal')"
            class="btn-secondary w-full sm:w-auto flex items-center justify-center gap-1 px-3 py-2"
          >
            📝 新建生成計畫
          </button> -->
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
  </ClientOnly>
</template>

<script setup>
// ===== 页面元数据 =====
// 设置中间件验证，确保用户已登陆
definePageMeta({
  middleware: "auth",
});

// ===== SEO 配置 =====
// 设置页面标题和元数据，用于搜索引擎优化
useHead({
  title: "數據生產工作室 - TGSA 補助引擎",
  meta: [
    {
      name: "description",
      content:
        "高效的數據生產工作室。支持批量 AI 生成、手動標註和計畫編輯，建立高品質計畫書數據集。",
    },
    {
      name: "keywords",
      content: "數據生產,AI 生成,標註,計畫,工作室",
    },
    {
      property: "og:title",
      content: "數據生產工作室 - TGSA 補助引擎",
    },
    {
      property: "og:description",
      content: "高效的數據生產工作室。支持批量 AI 生成、手動標註和計畫編輯。",
    },
  ],
});

// ===== 输入框模态框处理函数 =====
// 处理用户在输入框模态框中的提交操作（重命名或创建計畫）
async function handleInputModalSubmit(value) {
  isInputModalVisible.value = false;
  if (!value || !value.trim()) return;
  if (inputModalMode === "rename" && inputModalDraft) {
    // Rename draft
    if (value === inputModalDraft.name) return;
    try {
      const response = await authenticatedFetch(
        `${API_BASE_URL}/draft_plans/${inputModalDraft.id}`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ name: value }),
        },
      );
      if (!response.ok)
        throw new Error("重命名失败: " + (await response.text()));
      success(`計畫已重命名为 "${value}"`);
      fetchDrafts();
    } catch (e) {
      errorNotification(e.message);
    }
  } else if (inputModalMode === "create" && inputModalDraft) {
    // Create draft
    try {
      const response = await authenticatedFetch(`${API_BASE_URL}/draft_plans`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
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
  // 关闭输入框模态框
  isInputModalVisible.value = false;
  inputModalDraft = null;
}

// ===== 导入依赖库 =====
// 导入 Vue 核心库
import { ref, onMounted, onUnmounted } from "vue";
// 导入 Supabase 数据库客户端
import { supabase } from "~/utils/supabaseClient";
// 导入自定义组合式函数和通知服务
import { usePlanGenerator } from "~/composables/usePlanGenerator";
import { useNotifications } from "~/composables/useNotifications";
import { useConfirm } from "~/composables/useConfirm";
import { authenticatedFetch } from "~/composables/useAppAuth";
// 导入子组件
import DraftPlanList from "~/components/data/dataset/DraftPlanList.vue";
import BatchSyntheticModal from "~/components/data/dataset/BatchSyntheticModal.vue";
import DraftPlanEditorModal from "~/components/data/dataset/DraftPlanEditorModal.vue";
import InputPromptModal from "~/components/data/dataset/InputPromptModal.vue";
// 导入加载状态和动态模式生成工具
import { useLoading } from "~/composables/useLoading";
import { getDynamicFieldDefinitions } from "~/utils/dynamicSchema";

// ===== 模态框状态数据 =====
// 用于重命名或创建計畫的输入框模态框状态
const isInputModalVisible = ref(false);
const inputModalTitle = ref("");
const inputModalMessage = ref("");
const inputModalDefaultValue = ref("");
let inputModalMode = ""; // 'rename' 或 'create' 模式
let inputModalDraft = null;

const { success, error: errorNotification } = useNotifications();
const { confirm } = useConfirm();
const config = useRuntimeConfig();
const API_BASE_URL = `${config.public.apiBaseUrl}/api`;
const { show: showLoading, hide: hideLoading } = useLoading();
const { allConfigs, fetchAllConfigs } = usePlanGenerator();

// ===== 数据状态 =====
// 草稿列表、选中的草稿、批量模态框可见性状态
const drafts = ref([]);
const selectedDraft = ref(null);
const isBatchModalVisible = ref(false);
// 实时数据库频道引用，用于监听数据变化
let realtimeChannel = null;

// ===== 計畫编辑操作 =====
// 处理重命名計畫的模态框打开
async function handleRenameDraft(draft) {
  inputModalTitle.value = "重命名計畫";
  inputModalMessage.value = "请输入新的計畫名称:";
  inputModalDefaultValue.value = draft.name;
  inputModalMode = "rename";
  inputModalDraft = draft;
  isInputModalVisible.value = true;
}

// ===== 删除計畫 =====
// 显示确认对话框并删除选中的計畫
async function handleDeleteDraft(draft) {
  const isConfirmed = await confirm({
    title: "確認刪除計畫",
    message: `您確定要刪除計畫 "${draft.name}" 嗎？\n\n⚠️ 此操作無法撤銷。`,
    confirmText: "確認刪除",
    cancelText: "取消",
    confirmColor: "danger",
  });

  if (!isConfirmed) {
    return;
  }

  try {
    const response = await authenticatedFetch(
      `${API_BASE_URL}/draft_plans/${draft.id}`,
      {
        method: "DELETE",
      },
    );
    if (!response.ok) throw new Error("删除失败: " + (await response.text()));
    success(`計畫 "${draft.name}" 已被删除。`);
    fetchDrafts();
  } catch (e) {
    errorNotification(e.message);
  }
}

// ===== 获取草稿列表 =====
// 从数据库中获取所有計畫草稿，按创建时间倒序排列
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

// ===== 生命周期钩子 =====
// 页面挂载时，初始化配置和草稿列表，并监听实时数据变化
onMounted(async () => {
  const { checkIsInternal } = useInternalCheck();
  const isInternal = await checkIsInternal();
  if (!isInternal) {
    window.location.href = "/";
    return;
  }

  showLoading("加载中...");
  try {
    await fetchAllConfigs(); // Fetch configs for Batch modal
    await fetchDrafts();
    realtimeChannel = supabase
      .channel("ai_proposal_platform:draft_plans")
      .on(
        "postgres_changes",
        { event: "*", schema: "ai_proposal_platform", table: "draft_plans" },
        () => {
          fetchDrafts();
        },
      )
      .subscribe();
  } finally {
    hideLoading();
  }
});

// ===== 组件卸载 =====
// 页面卸载时，清理实时频道订阅
onUnmounted(() => {
  if (realtimeChannel) {
    supabase.removeChannel(realtimeChannel);
  }
});

// ===== 打开编辑器 =====
// 打开选中的計畫编辑器，初始化 user_input 和 plan_content 对象
function openEditor(draft) {
  // Make sure user_input and plan_content are valid objects
  if (!draft.user_input) draft.user_input = {};
  if (!draft.plan_content) draft.plan_content = {};
  selectedDraft.value = draft;
}

// ===== 创建計畫 =====
// 显示输入框模态框，用于创建新的計畫（手动标注或生成計畫）
async function handleCreateDraft(mode) {
  inputModalTitle.value = "新建計畫";
  inputModalMessage.value = `请输入新的計畫名称 (${
    mode === "golden" ? "手动标注" : "生成計畫"
  })：`;
  inputModalDefaultValue.value = "";
  inputModalMode = "create";
  inputModalDraft = mode;
  isInputModalVisible.value = true;
}

// ===== 批量 AI 生成 =====
// 启动批量 AI 生成任务，将新計畫添加到草稿列表
async function handleBatchStart(payload) {
  try {
    const schemaOptions = {
      templateId: payload.template_id,
      templateGrantId: payload.grant_id,
    };
    const dynamicFieldDefinitions = getDynamicFieldDefinitions(schemaOptions);
    if (!dynamicFieldDefinitions.length) {
      errorNotification(
        "批量生成失败：此模板尚未配置動態欄位，請先到 Section 管理設定欄位後再試。",
      );
      return;
    }

    const payload1 = {
      ...payload,
      dynamic_fields_schema: dynamicFieldDefinitions.map((definition) => ({
        label: definition.compositeKey,
      })),
    };
    const response = await authenticatedFetch(
      `${API_BASE_URL}/draft_plans/batch_synthetic`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload1),
      },
    );
    if (response.status !== 202) return;
    success(`已启动 ${payload1.count} 个 AI 生成任务，请关注列表状态更新。`);
  } catch (e) {
    console.error("Batch generation failed:", e);
  }
}

// ===== 保存到最终数据集 =====
// 将計畫保存到最终数据集，然后删除对应的草稿
async function handleSaveToFinalDataset(draftToSave, finalInputs) {
  const {
    id: draftId,
    plan_content,
    grant_id,
    template_id,
    mode,
  } = draftToSave;

  if (!plan_content || Object.keys(plan_content).length === 0) {
    errorNotification("計畫書内容为空，无法保存。");
    return;
  }

  // 顯示確認對話框
  const isConfirmed = await confirm({
    title: "確認保存至最終數據集",
    message: `您確定要保存計畫 "${draftToSave.name}" 至最終數據集嗎？\n\n⚠️ 保存後此數據將自動刪除。\n💾 建議先下載 Word 檔案計畫書。`,
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
    const draftResponse = await authenticatedFetch(
      `${API_BASE_URL}/draft_plans/${draftId}`,
      {
        headers: {
          "Content-Type": "application/json",
        },
      },
    );

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
            mode === "synthetic" || mode === "internal"
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

    const response = await authenticatedFetch(`${API_BASE_URL}/datasets`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ entries }),
    });
    if (response.status !== 202)
      throw new Error("保存至数据集失败: " + (await response.text()));

    success(`計畫 "${draftToSave.name}" 已成功保存至最终数据集！`);
    await authenticatedFetch(`${API_BASE_URL}/draft_plans/${draftId}`, {
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
