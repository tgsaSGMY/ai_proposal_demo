<!-- 計畫書版本預覽：與「下載報告」的 Word 文件相同版面（A4、上下左右 1 吋邊界）
     版本預覽（PlanVersionModal）與既有計畫點評的「選擇計畫」共用 -->
<template>
  <p v-if="configLoading" class="py-10 text-center text-sm text-slate-400">
    載入文件版面中...
  </p>
  <div
    v-else-if="documentHtml"
    class="word-page mx-auto rounded-2xl bg-[#fff7f3]"
    :style="scaleStyle"
    v-html="documentHtml"
  ></div>
  <p v-else class="py-10 text-center text-sm text-slate-400">
    此版本沒有可顯示的內容
  </p>
</template>

<script setup lang="ts">
import {
  fetchWordExportConfig,
  renderPlanToHtml,
  renderPlanToHtmlUsingWordConfig,
} from "~/utils/exportToWord";
import { scramblePlanSections } from "~/utils/demoScramble";

const props = withDefaults(
  defineProps<{
    planSections: any[];
    planData: Record<string, any> | null | undefined;
    // 以下參數與 exportPlanToWord 相同，用來選出同一份 Word 匯出設定
    grantId?: string;
    templateId?: string;
    projectTitle?: string;
    projectCreatedAt?: string;
    projectSectionVersions?: Record<string, number>;
    // 放大倍率（例如 1.25）；放大後寬度仍不超出外框
    scale?: number;
    // Demo：這些章節的內容以亂碼顯示（註冊後才可完整檢視）
    lockedSectionIds?: string[];
  }>(),
  {
    grantId: "",
    templateId: "",
    projectTitle: "",
    projectCreatedAt: "",
    projectSectionVersions: undefined,
    scale: 1,
    lockedSectionIds: () => [],
  },
);

// Demo：鎖定章節先換成亂碼再排版，版面與下載的 Word 相同但內容不可讀
const displayPlanData = computed(() =>
  scramblePlanSections(props.planData, props.lockedSectionIds),
);

const scaleStyle = computed(() =>
  props.scale === 1
    ? undefined
    : { zoom: props.scale, maxWidth: `${100 / props.scale}%` },
);

// Word 匯出設定：與「下載報告」使用同一份
const exportConfig = ref<any>(null);
const configLoading = ref(false);
let loadedConfigKey = "";

watch(
  () => [
    props.grantId,
    props.templateId,
    props.projectCreatedAt,
    props.projectSectionVersions,
  ],
  async () => {
    const key = JSON.stringify([
      props.grantId,
      props.templateId,
      props.projectCreatedAt,
      props.projectSectionVersions,
    ]);
    if (key === loadedConfigKey) return;
    loadedConfigKey = key;
    configLoading.value = true;
    try {
      const config = await fetchWordExportConfig(
        props.grantId,
        props.templateId,
        props.projectCreatedAt || undefined,
        props.projectSectionVersions,
      );
      if (loadedConfigKey === key) exportConfig.value = config;
    } finally {
      if (loadedConfigKey === key) configLoading.value = false;
    }
  },
  { immediate: true },
);

// 整份文件的 HTML：有匯出設定時依設定排版，否則與預設 Word 匯出一致
const documentHtml = computed(() => {
  const planData = displayPlanData.value;
  if (!planData || !props.planSections?.length) {
    return "";
  }
  try {
    if (exportConfig.value) {
      return renderPlanToHtmlUsingWordConfig(
        exportConfig.value,
        props.planSections,
        planData,
        props.projectTitle || undefined,
      );
    }
    return renderPlanToHtml(
      props.planSections,
      planData,
      props.projectTitle || undefined,
    );
  } catch (error) {
    console.error("無法渲染文件預覽", error);
    return "";
  }
});
</script>

<style scoped>
/* 模擬 Word 頁面：A4 寬、1 吋邊界（行高與段落間距由各段落的 inline style 決定） */
.word-page {
  box-sizing: border-box;
  width: 210mm;
  max-width: 100%;
  padding: 1in;
  color: #000;
}

.word-page :deep(p) {
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

/* Word 表格：寬 100%、0.5pt 黑色單線框、文字幾乎貼齊框線（實測約 1.5pt） */
.word-page :deep(table) {
  width: 100%;
  border-collapse: collapse;
  table-layout: auto;
}

.word-page :deep(td) {
  border: 0.5pt solid #000;
  padding: 0 1.5pt;
  vertical-align: top;
}

@media (max-width: 640px) {
  .word-page {
    padding: 16px;
  }
}
</style>
