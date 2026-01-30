<template>
  <div
    v-if="isVisible && template"
    class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 px-4 py-6"
    @click.self="emit('close')"
  >
    <section
      class="w-full max-w-8xl max-h-full overflow-y-auto rounded-2xl bg-white p-6 space-y-6 shadow-2xl"
    >
      <header class="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p
            class="text-xs font-semibold text-rose-400 uppercase tracking-[0.3em]"
          >
            Word Export Editor
          </p>
          <h2 class="text-2xl font-bold text-slate-900">
            {{ template.name }} · {{ template.id }}
          </h2>
          <p class="text-sm text-slate-500">
            設定 Word
            樣式、段落字體與表格欄位，儲存後會產生新版本供專案匯出時比對使用。
          </p>
        </div>
        <button
          type="button"
          class="text-2xl font-bold text-slate-400 hover:text-slate-600"
          @click="emit('close')"
        >
          ×
        </button>
      </header>

      <div class="grid gap-6 lg:grid-cols-[1fr,1fr]">
        <div class="space-y-6 overflow-y-auto max-h-[calc(100vh-12rem)]">
          <aside
            class="space-y-3 rounded-2xl border border-slate-200 bg-slate-50 p-4"
          >
            <div class="flex items-center justify-between">
              <h3 class="text-sm font-semibold text-slate-700">版本歷史</h3>
              <span class="text-xs text-slate-500"
                >{{ versionHistory.length }} 筆</span
              >
            </div>
            <p class="text-xs text-slate-500">
              系統會依專案建立時間，找出當時最近的版本。若尚未建立版本，匯出時將落回預設版型。
            </p>
            <ul class="space-y-2 text-sm">
              <li
                v-for="version in versionHistory"
                :key="version.id"
                class="rounded-xl border border-slate-200 bg-white p-3"
              >
                <div class="flex items-center justify-between gap-2">
                  <div>
                    <p class="font-semibold text-slate-800">
                      {{ formatDate(version.createdAt) }}
                    </p>
                    <p class="text-xs text-slate-500 truncate">
                      {{ version.createdBy || "未記錄" }}
                    </p>
                  </div>
                  <button
                    type="button"
                    class="text-xs font-semibold text-rose-600 hover:text-rose-700"
                    @click="applyVersion(version)"
                  >
                    套用
                  </button>
                </div>
              </li>
              <li v-if="!versionHistory.length" class="text-xs text-slate-400">
                尚未建立任何版本。
              </li>
            </ul>
          </aside>

          <section class="rounded-2xl border border-slate-200 p-4 space-y-4">
            <div class="flex items-center justify-between">
              <h3 class="text-base font-semibold text-slate-800">
                文件字體設定
              </h3>
            </div>
            <div class="grid gap-4 md:grid-cols-3">
              <label class="space-y-1 text-sm text-slate-600">
                標題字體
                <select
                  v-model="formState.documentStyle.headingFont"
                  class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
                >
                  <option
                    v-for="font in FONT_OPTIONS"
                    :key="font"
                    :value="font"
                  >
                    {{ font }}
                  </option>
                </select>
              </label>
              <label class="space-y-1 text-sm text-slate-600">
                標題大小 (pt)
                <input
                  v-model.number="formState.documentStyle.headingSizePt"
                  type="number"
                  min="8"
                  class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
                />
              </label>
              <label class="flex items-center gap-2 text-sm text-slate-600">
                <input
                  v-model="formState.documentStyle.headingBold"
                  type="checkbox"
                  class="h-4 w-4 rounded border-slate-300"
                />
                標題加粗
              </label>
              <label class="space-y-1 text-sm text-slate-600">
                小標字體
                <select
                  v-model="formState.documentStyle.subHeadingFont"
                  class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
                >
                  <option
                    v-for="font in FONT_OPTIONS"
                    :key="font"
                    :value="font"
                  >
                    {{ font }}
                  </option>
                </select>
              </label>
              <label class="space-y-1 text-sm text-slate-600">
                小標大小 (pt)
                <input
                  v-model.number="formState.documentStyle.subHeadingSizePt"
                  type="number"
                  min="8"
                  class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
                />
              </label>
              <label class="flex items-center gap-2 text-sm text-slate-600">
                <input
                  v-model="formState.documentStyle.subHeadingBold"
                  type="checkbox"
                  class="h-4 w-4 rounded border-slate-300"
                />
                小標加粗
              </label>
              <label class="space-y-1 text-sm text-slate-600">
                內文字體
                <select
                  v-model="formState.documentStyle.bodyFont"
                  class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
                >
                  <option
                    v-for="font in FONT_OPTIONS"
                    :key="font"
                    :value="font"
                  >
                    {{ font }}
                  </option>
                </select>
              </label>
              <label class="space-y-1 text-sm text-slate-600">
                內文大小 (pt)
                <input
                  v-model.number="formState.documentStyle.bodySizePt"
                  type="number"
                  min="8"
                  class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
                />
              </label>
              <label class="flex items-center gap-2 text-sm text-slate-600">
                <input
                  v-model="formState.documentStyle.bodyBold"
                  type="checkbox"
                  class="h-4 w-4 rounded border-slate-300"
                />
                內文加粗
              </label>
            </div>
          </section>

          <section class="rounded-2xl border border-slate-200 p-4 space-y-4">
            <div class="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h3 class="text-base font-semibold text-slate-800">
                  文檔章節流程
                </h3>
                <p class="text-xs text-slate-500">
                  建立節點樹以控制標題、段落、表格、清單與條件顯示，匯出時會依序渲染。
                </p>
              </div>
              <div class="flex flex-col gap-2 sm:flex-row">
                <button
                  type="button"
                  class="rounded-lg border border-slate-300 px-3 py-1 text-sm font-semibold text-slate-700 hover:bg-slate-50"
                  @click="addNode()"
                >
                  新增章節
                </button>
              </div>
            </div>

            <div
              v-if="!(formState.nodes && formState.nodes.length)"
              class="rounded-xl border border-dashed border-slate-300 bg-slate-50/60 p-6 text-center text-sm text-slate-500"
            >
              尚未建立節點，點擊「新增節點」開始設定自訂輸出流程。
            </div>

            <div v-else class="space-y-4">
              <div
                class="flex items-center gap-2 overflow-x-auto rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm"
              >
                <button
                  v-for="chapter in groupedNodes"
                  :key="`tab-${chapter.id}`"
                  type="button"
                  class="shrink-0 rounded-xl px-3 py-1 font-semibold"
                  :class="[
                    selectedChapterId === chapter.id
                      ? 'bg-rose-500 text-white'
                      : 'text-slate-600 hover:text-rose-500',
                  ]"
                  @click="selectedChapterId = chapter.id"
                >
                  {{ chapter.title || "未命名章節" }}
                </button>
              </div>

              <details
                v-for="(chapter, chapterIndex) in filteredChapters"
                :key="chapter.id"
                class="rounded-2xl border border-slate-200 bg-white overflow-hidden"
                :open="chapterIndex === 0"
              >
                <summary
                  class="flex items-center justify-between p-4 cursor-pointer hover:bg-slate-50"
                >
                  <div class="flex items-center gap-3">
                    <span class="text-sm font-semibold text-slate-700">{{
                      chapter.title || "未命名章節"
                    }}</span>
                    <span class="text-xs text-slate-500"
                      >({{ chapter.contentNodes.length }} 個節點)</span
                    >
                  </div>
                  <div class="flex items-center gap-2">
                    <button
                      type="button"
                      class="text-xs text-slate-600 hover:text-slate-700 rounded-lg border border-slate-200 px-2 py-1"
                      @click.stop="editChapterTitle(chapter.id)"
                      title="編輯章節標題"
                    >
                      編輯
                    </button>
                    <button
                      type="button"
                      class="text-xs rounded-lg border border-slate-200 px-2 py-1 text-slate-600 disabled:opacity-40"
                      :disabled="getChapterGlobalIndex(chapter.id) === 0"
                      @click.stop="moveChapter(chapter.id, 'up')"
                      title="上移章節"
                    >
                      ↑
                    </button>
                    <button
                      type="button"
                      class="text-xs rounded-lg border border-slate-200 px-2 py-1 text-slate-600 disabled:opacity-40"
                      :disabled="
                        getChapterGlobalIndex(chapter.id) ===
                        groupedNodes.length - 1
                      "
                      @click.stop="moveChapter(chapter.id, 'down')"
                      title="下移章節"
                    >
                      ↓
                    </button>
                    <button
                      type="button"
                      class="text-xs text-rose-600 hover:text-rose-700 rounded-lg border border-rose-200 px-2 py-1"
                      @click.stop="removeChapter(chapter.id)"
                      title="刪除章節"
                    >
                      刪除
                    </button>
                  </div>
                </summary>
                <div class="p-4 space-y-4 border-t border-slate-200">
                  <div
                    v-for="(node, nodeIndex) in chapter.contentNodes"
                    :key="node.id"
                    class="rounded-xl border border-slate-200 p-4 space-y-4 bg-white"
                  >
                    <div
                      class="flex flex-wrap items-center justify-between gap-3"
                    >
                      <label class="flex-1 space-y-1 text-sm text-slate-600">
                        <span class="text-xs font-semibold text-slate-500">
                          節點類型
                        </span>
                        <select
                          v-model="node.type"
                          class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
                          @change="handleNodeTypeChange(node.id)"
                        >
                          <option
                            v-for="option in NODE_TYPE_OPTIONS"
                            :key="option.value"
                            :value="option.value"
                          >
                            {{ option.label }}
                          </option>
                        </select>
                      </label>
                      <div class="flex items-center gap-2 text-xs">
                        <button
                          type="button"
                          class="rounded-lg border border-slate-200 px-2 py-1 text-slate-600 disabled:opacity-40"
                          :disabled="nodeIndex === 0"
                          @click="moveNode(node.id, 'up')"
                        >
                          上移
                        </button>
                        <button
                          type="button"
                          class="rounded-lg border border-slate-200 px-2 py-1 text-slate-600 disabled:opacity-40"
                          :disabled="
                            nodeIndex === chapter.contentNodes.length - 1
                          "
                          @click="moveNode(node.id, 'down')"
                        >
                          下移
                        </button>
                        <button
                          type="button"
                          class="rounded-lg border border-rose-200 px-2 py-1 text-rose-600"
                          @click="removeNode(node.id)"
                        >
                          刪除
                        </button>
                      </div>
                    </div>

                    <div
                      v-if="shouldShowNodeLabel(node)"
                      class="space-y-1 text-sm text-slate-600"
                    >
                      <span class="text-xs font-semibold text-slate-500"
                        >節點標題</span
                      >
                      <input
                        v-model="node.label"
                        type="text"
                        class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
                        placeholder="例如：壹、申請業者簡介"
                      />
                    </div>

                    <div
                      v-if="shouldShowSectionSelectors(node)"
                      class="grid gap-4 md:grid-cols-2"
                    >
                      <label class="space-y-1 text-sm text-slate-600">
                        資料章節
                        <select
                          v-model="node.sectionId"
                          class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
                          @change="handleNodeSectionChange(node.id)"
                        >
                          <option value="">無資料來源（純文字）</option>
                          <option
                            v-for="option in sectionOptions"
                            :key="option.value"
                            :value="option.value"
                          >
                            {{ option.label }}
                          </option>
                        </select>
                      </label>
                      <label class="space-y-1 text-sm text-slate-600">
                        資料欄位
                        <div class="space-y-2">
                          <!-- Cascading dropdowns for nested data path selection -->
                          <template v-if="shouldShowSectionSelectors(node)">
                            <div
                              v-for="(
                                levelOptions, levelIndex
                              ) in getDataPathLevels(node)"
                              :key="`level-${levelIndex}`"
                              class="flex items-center gap-2"
                            >
                              <select
                                :value="
                                  parseDataPath(node.dataPath)[levelIndex] || ''
                                "
                                class="flex-1 rounded-xl border border-slate-200 px-3 py-2 text-sm"
                                @change="
                                  (event) =>
                                    handleDataPathLevelChange(
                                      node.id,
                                      levelIndex,
                                      (event.target as HTMLSelectElement).value,
                                    )
                                "
                              >
                                <option value="">
                                  {{
                                    levelIndex === 0
                                      ? "整個章節/物件"
                                      : "選擇子欄位..."
                                  }}
                                </option>
                                <option
                                  v-for="option in levelOptions"
                                  :key="option.value"
                                  :value="option.value"
                                >
                                  {{ option.label }}
                                </option>
                              </select>
                              <!-- Add button to drill deeper if possible -->
                              <button
                                v-if="
                                  levelIndex ===
                                    parseDataPath(node.dataPath).length - 1 &&
                                  canNestDeeper(node)
                                "
                                type="button"
                                class="px-3 py-2 text-sm font-semibold text-rose-600 hover:text-rose-700 rounded-xl border border-rose-200 hover:bg-rose-50"
                                @click="handleAddDataPathLevel(node.id)"
                                title="新增一層巢狀欄位"
                              >
                                +
                              </button>
                            </div>
                          </template>
                          <!-- Simple option when section not selected -->
                          <select
                            v-if="!shouldShowSectionSelectors(node)"
                            v-model="node.dataPath"
                            class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
                            @change="handleNodeDataPathChange(node.id)"
                          >
                            <option value="">無法選擇（需先選擇章節）</option>
                          </select>
                        </div>
                      </label>
                    </div>

                    <div
                      v-if="shouldShowTemplateInput(node)"
                      class="space-y-1 text-sm text-slate-600"
                    >
                      <span class="text-xs font-semibold text-slate-500"
                        >自訂文字</span
                      >
                      <textarea
                        v-model="node.template"
                        rows="3"
                        class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
                        placeholder="輸入要顯示的內容"
                      ></textarea>
                    </div>

                    <label
                      v-if="
                        node.type === 'paragraph' || node.type === 'customText'
                      "
                      class="flex items-center gap-2 text-sm text-slate-600 cursor-pointer"
                    >
                      <input
                        type="checkbox"
                        class="h-4 w-4 rounded border-slate-300"
                        :checked="node.style?.bodyBold === true"
                        @change="
                          (event) =>
                            handleNodeBoldToggle(
                              node.id,
                              (event.target as HTMLInputElement).checked,
                            )
                        "
                      />
                      使用粗體
                    </label>

                    <div
                      v-if="node.type === 'paragraph'"
                      class="flex flex-wrap items-center gap-2 text-sm text-slate-600"
                    >
                      <label class="flex items-center gap-2 cursor-pointer">
                        <input
                          type="checkbox"
                          class="h-4 w-4 rounded border-slate-300"
                          :checked="node.paragraphNumbering === true"
                          @change="
                            (event) =>
                              handleParagraphNumberingToggle(
                                node.id,
                                (event.target as HTMLInputElement).checked,
                              )
                          "
                        />
                        使用編號
                      </label>
                      <select
                        v-if="node.paragraphNumbering"
                        v-model="node.paragraphNumberStyle"
                        class="rounded-xl border border-slate-200 px-3 py-1 text-xs"
                      >
                        <option
                          v-for="option in LIST_STYLE_OPTIONS"
                          :key="option.value"
                          :value="option.value"
                        >
                          {{ option.label }}
                        </option>
                      </select>
                    </div>

                    <div
                      v-if="node.type === 'table'"
                      class="space-y-3 rounded-xl bg-slate-50 p-3"
                    >
                      <label
                        class="flex items-center gap-2 text-sm text-slate-600"
                      >
                        <input
                          v-model="ensureTableConfig(node).customHeaders"
                          type="checkbox"
                          class="h-4 w-4 rounded border-slate-300"
                        />
                        啟用自定義列標題
                      </label>
                      <label
                        class="flex items-center gap-2 text-sm text-slate-600"
                      >
                        <input
                          v-model="ensureTableConfig(node).transpose"
                          type="checkbox"
                          class="h-4 w-4 rounded border-slate-300"
                        />
                        倒置表格（列↔欄互換）
                      </label>

                      <div
                        v-if="
                          node.table?.customHeaders &&
                          node.table?.columns?.length
                        "
                        class="space-y-2 border-t border-slate-200 pt-3"
                      >
                        <p class="text-xs font-semibold text-slate-500">
                          自定義列標題
                        </p>
                        <div class="space-y-2">
                          <div
                            v-for="(column, colIndex) in node.table.columns"
                            :key="column.key"
                            class="flex items-center gap-2"
                          >
                            <input
                              v-model="column.label"
                              type="text"
                              class="flex-1 rounded-xl border border-slate-200 px-3 py-2 text-sm"
                              :placeholder="`列 ${colIndex + 1} 標題`"
                            />
                            <span
                              class="text-xs text-slate-500 whitespace-nowrap"
                              >({{ column.key }})</span
                            >
                            <div class="flex items-center gap-1">
                              <button
                                type="button"
                                class="rounded-lg border border-slate-200 px-2 py-1 text-xs text-slate-600 disabled:opacity-40"
                                :disabled="colIndex === 0"
                                @click="
                                  moveTableColumn(node.id, colIndex, 'up')
                                "
                                title="上移列"
                              >
                                ↑
                              </button>
                              <button
                                type="button"
                                class="rounded-lg border border-slate-200 px-2 py-1 text-xs text-slate-600 disabled:opacity-40"
                                :disabled="
                                  colIndex === node.table.columns.length - 1
                                "
                                @click="
                                  moveTableColumn(node.id, colIndex, 'down')
                                "
                                title="下移列"
                              >
                                ↓
                              </button>
                            </div>
                          </div>
                        </div>
                      </div>

                      <div>
                        <p class="text-xs font-semibold text-slate-500">
                          欄位內容
                        </p>
                        <div class="mt-2 grid gap-2 md:grid-cols-2">
                          <label
                            v-for="option in getNodeColumnCandidates(node)"
                            :key="option.key"
                            class="flex items-center gap-2 rounded-xl border border-slate-200 px-3 py-2 text-sm"
                          >
                            <input
                              type="checkbox"
                              :checked="
                                node.table?.columns?.some(
                                  (column) => column.key === option.key,
                                )
                              "
                              class="h-4 w-4 rounded border-slate-300"
                              @change="
                                (event) =>
                                  onNodeColumnToggle(node.id, option, event)
                              "
                            />
                            <span class="truncate"
                              >{{ option.label }} ({{ option.key }})</span
                            >
                          </label>
                        </div>
                        <p
                          v-if="!getNodeColumnCandidates(node).length"
                          class="text-xs text-slate-400 mt-2"
                        >
                          無可用欄位，請確認章節或資料來源設定。
                        </p>
                      </div>
                    </div>

                    <div
                      v-if="node.type === 'customTable'"
                      class="space-y-4 rounded-xl bg-slate-50 p-3"
                    >
                      <div class="grid gap-3 md:grid-cols-2">
                        <label class="space-y-1 text-sm text-slate-600">
                          列數 (1-20)
                          <input
                            :value="node.customTable?.rows ?? 1"
                            type="number"
                            min="1"
                            max="20"
                            class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
                            @change="
                              (event) =>
                                handleCustomTableDimensionChange(
                                  node.id,
                                  'rows',
                                  Number(
                                    (event.target as HTMLInputElement | null)
                                      ?.value || 1,
                                  ),
                                )
                            "
                          />
                        </label>
                        <label class="space-y-1 text-sm text-slate-600">
                          欄數 (1-6)
                          <input
                            :value="node.customTable?.cols ?? 1"
                            type="number"
                            min="1"
                            max="6"
                            class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
                            @change="
                              (event) =>
                                handleCustomTableDimensionChange(
                                  node.id,
                                  'cols',
                                  Number(
                                    (event.target as HTMLInputElement | null)
                                      ?.value || 1,
                                  ),
                                )
                            "
                          />
                        </label>
                      </div>

                      <div class="space-y-3">
                        <div
                          v-for="rowIndex in node.customTable?.rows || 0"
                          :key="`custom-row-${node.id}-${rowIndex}`"
                          class="space-y-2"
                        >
                          <p class="text-xs font-semibold text-slate-500">
                            第 {{ rowIndex }} 列
                          </p>
                          <div
                            class="grid gap-3"
                            :style="{
                              gridTemplateColumns:
                                'repeat(' +
                                (node.customTable?.cols || 1) +
                                ', minmax(0, 1fr))',
                            }"
                          >
                            <div
                              v-for="cell in getCustomTableRowCells(
                                node,
                                rowIndex - 1,
                              )"
                              :key="cell.id"
                              class="rounded-xl border border-slate-200 p-3 space-y-2 bg-white"
                            >
                              <p class="text-xs font-semibold text-slate-500">
                                儲存格 {{ rowIndex }}-{{ cell.col + 1 }}
                              </p>
                              <div class="space-y-2">
                                <div
                                  v-for="(
                                    content, contentIndex
                                  ) in cell.contents"
                                  :key="content.id"
                                  class="rounded-lg border border-slate-200 p-2 space-y-2"
                                >
                                  <div
                                    class="flex flex-wrap items-center justify-between gap-2"
                                  >
                                    <div
                                      class="flex items-center gap-2 text-xs text-slate-500"
                                    >
                                      <span>片段 {{ contentIndex + 1 }}</span>
                                      <select
                                        v-model="content.type"
                                        class="rounded-lg border border-slate-200 px-2 py-1 text-xs"
                                        @change="
                                          handleCustomTableCellContentTypeChange(
                                            cell,
                                            content,
                                          )
                                        "
                                      >
                                        <option value="text">自訂文字</option>
                                        <option value="field">資料欄位</option>
                                      </select>
                                    </div>
                                    <div class="flex items-center gap-1">
                                      <button
                                        type="button"
                                        class="rounded-lg border border-slate-200 px-2 py-1 text-xs text-slate-600 disabled:opacity-40"
                                        :disabled="contentIndex === 0"
                                        @click="
                                          moveCustomTableCellContent(
                                            cell,
                                            contentIndex,
                                            'up',
                                          )
                                        "
                                        title="上移片段"
                                      >
                                        ↑
                                      </button>
                                      <button
                                        type="button"
                                        class="rounded-lg border border-slate-200 px-2 py-1 text-xs text-slate-600 disabled:opacity-40"
                                        :disabled="
                                          contentIndex ===
                                          (cell.contents?.length || 0) - 1
                                        "
                                        @click="
                                          moveCustomTableCellContent(
                                            cell,
                                            contentIndex,
                                            'down',
                                          )
                                        "
                                        title="下移片段"
                                      >
                                        ↓
                                      </button>
                                      <button
                                        type="button"
                                        class="rounded-lg border border-rose-200 px-2 py-1 text-xs text-rose-600 disabled:opacity-40"
                                        :disabled="
                                          (cell.contents?.length || 0) === 1
                                        "
                                        @click="
                                          removeCustomTableCellContent(
                                            cell,
                                            content.id,
                                          )
                                        "
                                        title="刪除此片段"
                                      >
                                        刪除
                                      </button>
                                    </div>
                                  </div>
                                  <div
                                    v-if="content.type === 'text'"
                                    class="space-y-1"
                                  >
                                    <span class="text-xs text-slate-500"
                                      >顯示文字</span
                                    >
                                    <input
                                      v-model="content.text"
                                      type="text"
                                      class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
                                      placeholder="輸入內容"
                                      @input="
                                        syncLegacyCustomTableCellFields(cell)
                                      "
                                    />
                                  </div>
                                  <div v-else class="space-y-1">
                                    <span class="text-xs text-slate-500"
                                      >資料欄位</span
                                    >
                                    <select
                                      v-model="content.dataPath"
                                      class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
                                      @change="
                                        syncLegacyCustomTableCellFields(cell)
                                      "
                                    >
                                      <option value="">選擇欄位</option>
                                      <option
                                        v-for="option in getNodeColumnCandidates(
                                          node,
                                        )"
                                        :key="option.key"
                                        :value="option.key"
                                      >
                                        {{ option.label }}
                                      </option>
                                    </select>
                                    <p
                                      v-if="
                                        !getNodeColumnCandidates(node).length &&
                                        node.sectionId
                                      "
                                      class="text-xs text-slate-400"
                                    >
                                      無可用欄位，請調整資料來源。
                                    </p>
                                    <p
                                      v-if="!node.sectionId"
                                      class="text-xs text-rose-500"
                                    >
                                      需先選擇資料章節才能綁定欄位。
                                    </p>
                                  </div>
                                </div>
                                <div class="flex flex-wrap gap-2 pt-1">
                                  <button
                                    type="button"
                                    class="rounded-lg border border-slate-200 px-3 py-1 text-xs text-slate-600 hover:bg-slate-50"
                                    @click="
                                      addCustomTableCellContent(cell, 'text')
                                    "
                                  >
                                    + 新增文字片段
                                  </button>
                                  <button
                                    type="button"
                                    class="rounded-lg border border-slate-200 px-3 py-1 text-xs text-slate-600 hover:bg-slate-50 disabled:opacity-40"
                                    :disabled="!node.sectionId"
                                    @click="
                                      addCustomTableCellContent(cell, 'field')
                                    "
                                  >
                                    + 新增資料片段
                                  </button>
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>

                    <div
                      v-if="node.type === 'list' || node.type === 'subHeading'"
                      class="space-y-3 rounded-xl bg-slate-50 p-3"
                    >
                      <label
                        class="flex items-center gap-2 text-sm text-slate-600"
                      >
                        <input
                          v-model="ensureListConfig(node).numbering"
                          type="checkbox"
                          class="h-4 w-4 rounded border-slate-300"
                        />
                        使用編號
                      </label>
                      <label class="space-y-1 text-sm text-slate-600">
                        清單樣式
                        <select
                          v-model="ensureListConfig(node).style"
                          class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
                        >
                          <option
                            v-for="option in LIST_STYLE_OPTIONS"
                            :key="option.value"
                            :value="option.value"
                          >
                            {{ option.label }}
                          </option>
                        </select>
                      </label>

                      <div
                        v-if="node.type === 'list'"
                        class="border-t border-slate-200 pt-3 mt-3"
                      >
                        <label
                          class="flex items-center gap-2 text-sm text-slate-600 mb-2"
                        >
                          <input
                            v-model="ensureListItemConfig(node).useSubNodes"
                            type="checkbox"
                            class="h-4 w-4 rounded border-slate-300"
                          />
                          使用子節點渲染對象（嵌套清單）
                        </label>
                        <p class="text-xs text-slate-500 mb-3">
                          當清單項是對象時，使用子節點定義如何渲染每個字段
                        </p>

                        <div
                          v-if="node.list?.itemConfig?.useSubNodes"
                          class="space-y-3"
                        >
                          <button
                            type="button"
                            class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm hover:bg-slate-50"
                            @click="addListNodeChild(node.id)"
                          >
                            + 添加子節點
                          </button>

                          <RecursiveNodeEditor
                            v-for="childNode in node.children"
                            :key="childNode.id"
                            :node="childNode"
                            :parent-node-id="node.id"
                            :parent-level="
                              node.level != null
                                ? Math.max(node.level - 1, 0)
                                : 0
                            "
                            :section-options="sectionOptions"
                            :sections="sections"
                            :level="0"
                            :node-type-options="NODE_TYPE_OPTIONS"
                            :list-style-options="LIST_STYLE_OPTIONS"
                            @update="handleRecursiveNodeUpdate"
                            @remove="handleRecursiveNodeRemove"
                            @add-child="handleRecursiveNodeAddChild"
                          />
                        </div>
                      </div>
                    </div>
                    <div class="flex justify-end pt-2">
                      <button
                        type="button"
                        class="rounded-lg border border-slate-300 px-3 py-1 text-xs font-semibold text-slate-600 hover:bg-slate-50"
                        @click="addNodeAfterNode(node.id, chapter.id)"
                      >
                        + 新增節點
                      </button>
                    </div>
                  </div>

                  <div
                    class="flex justify-end pt-2"
                    v-if="chapter.contentNodes.length === 0"
                  >
                    <button
                      type="button"
                      class="rounded-lg border border-slate-300 px-3 py-1 text-xs font-semibold text-slate-600 hover:bg-slate-50"
                      @click="addNodeToChapter(chapter.id)"
                    >
                      + 新增節點
                    </button>
                  </div>
                </div>
              </details>

              <div class="flex justify-center pt-2">
                <button
                  type="button"
                  class="text-xs text-rose-600 hover:text-rose-700 font-semibold"
                  @click="addChapterMarker"
                >
                  + 添加章節分組
                </button>
              </div>
            </div>
          </section>
        </div>

        <aside
          class="rounded-2xl border border-slate-200 bg-slate-50 p-4 flex flex-col lg:sticky lg:top-6 max-h-[calc(100vh-12rem)]"
        >
          <div class="flex items-center justify-between mb-3 flex-shrink-0">
            <h3 class="text-sm font-semibold text-slate-700">即時預覽</h3>
          </div>
          <p class="text-xs text-slate-500 mb-4 flex-shrink-0">
            預覽文檔的渲染效果，會即時反映您的更改。
          </p>
          <div
            class="rounded-xl border border-slate-200 bg-white overflow-auto flex-1 min-h-0"
            ref="previewContainerRef"
          >
            <iframe
              ref="previewIframeRef"
              :srcdoc="debouncedPreviewHtml"
              class="w-full h-full border-0"
              title="文檔預覽"
              @load="handleIframeLoad"
            />
          </div>
        </aside>
      </div>

      <div class="flex flex-col gap-3 pt-2 sm:flex-row sm:justify-end">
        <button
          type="button"
          class="w-full sm:w-auto rounded-xl border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-600 hover:bg-slate-50"
          @click="emit('close')"
        >
          取消
        </button>
        <button
          type="button"
          class="w-full sm:w-auto rounded-xl border border-blue-300 px-4 py-2 text-sm font-semibold text-blue-600 hover:bg-blue-50"
          @click="handlePreviewExport"
        >
          預覽導出
        </button>
        <button
          type="button"
          class="w-full sm:w-auto rounded-xl border border-green-300 px-4 py-2 text-sm font-semibold text-green-600 hover:bg-green-50"
          @click="handleDownloadWord"
        >
          下載 Word
        </button>
        <button
          type="button"
          class="w-full sm:w-auto rounded-xl bg-rose-500 px-4 py-2 text-sm font-semibold text-white hover:bg-rose-600 disabled:opacity-50"
          :disabled="saving"
          @click="handleSave"
        >
          {{ saving ? "儲存中..." : "儲存為新版本" }}
        </button>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch, onMounted, nextTick } from "vue";
import type { PropType } from "vue";
import { useNotifications } from "~/composables/useNotifications";
import RecursiveNodeEditor from "./RecursiveNodeEditor.vue";
import type {
  WordDocumentNode,
  WordDocumentNodeType,
  WordExportConfigEntry,
  WordExportTemplateConfig,
  WordTableColumn,
  WordListStyle,
  WordCustomTableConfig,
  WordCustomTableCell,
  WordCustomTableCellContent,
  WordCustomTableCellContentType,
} from "~/types/wordExport";
import {
  Document,
  Packer,
  Paragraph,
  Table,
  TableCell,
  TableRow,
  TextRun,
  AlignmentType,
  UnderlineType,
  convertInchesToTwip,
} from "docx";

interface TemplateRecord {
  id: string;
  name: string;
  word_export_config?: WordExportConfigEntry[] | null;
}

interface SchemaField {
  title?: string;
  type?: string;
  properties?: Record<string, SchemaField>;
  items?: {
    properties?: Record<string, SchemaField>;
  };
}

interface SectionRecord {
  id: string;
  name: string;
  json_schema?: {
    properties?: Record<string, SchemaField>;
  } | null;
}

const DEFAULT_STYLE = {
  headingFont: "Times New Roman",
  headingSizePt: 18,
  headingBold: true,
  subHeadingFont: "Times New Roman",
  subHeadingSizePt: 14,
  subHeadingBold: true,
  bodyFont: "Times New Roman",
  bodySizePt: 12,
  bodyBold: false,
};

const props = defineProps({
  isVisible: { type: Boolean, default: false },
  template: {
    type: Object as PropType<TemplateRecord | null>,
    default: null,
  },
  sections: {
    type: Array as PropType<SectionRecord[]>,
    default: () => [],
  },
  saving: { type: Boolean, default: false },
});

const emit = defineEmits<{
  (e: "close"): void;
  (e: "save", payload: WordExportTemplateConfig): void;
}>();

const { error: notifyError } = useNotifications();

const FONT_OPTIONS = [
  "Times New Roman",
  "Arial",
  "Calibri",
  "Courier New",
  "Georgia",
  "Verdana",
  "宋體",
  "微軟雅黑",
  "黑體",
];

const NODE_TYPE_OPTIONS: Array<{ label: string; value: WordDocumentNodeType }> =
  [
    { label: "次標題", value: "subHeading" },
    { label: "段落文字", value: "paragraph" },
    { label: "表格", value: "table" },
    { label: "自訂表格", value: "customTable" },
    { label: "清單", value: "list" },
    { label: "自訂文字", value: "customText" },
  ];

const LIST_STYLE_OPTIONS = [
  { label: "一、 二、 三、", value: "chineseNumber" },
  { label: "1. 2. 3.", value: "arabicNumber" },
  { label: "（1）、（2）、（3）", value: "parenNumbered" },
  { label: "• ◦ ▪", value: "bullet" },
];

type HeadingCounterState = Record<number, number>;

function createHeadingCounterState(): HeadingCounterState {
  return {};
}

function resetHeadingCounters(state: HeadingCounterState) {
  Object.keys(state).forEach((key) => delete state[Number(key)]);
}

function formatChineseNumeral(value: number): string {
  if (value <= 0) return "";
  const digits = ["零", "一", "二", "三", "四", "五", "六", "七", "八", "九"];
  if (value <= 10) {
    return value === 10 ? "十" : digits[value] || "";
  }
  if (value < 20) {
    return `十${digits[value - 10]}`;
  }
  if (value < 100) {
    const tens = Math.floor(value / 10);
    const units = value % 10;
    let result = `${digits[tens]}十`;
    if (units !== 0) {
      result += digits[units];
    }
    return result;
  }
  // Fallback for large numbers - simple decimal representation
  return String(value);
}

function getImplicitLevelFromStyle(style: WordListStyle): number {
  switch (style) {
    case "chineseNumber": // 一、二、三、
    case "chineseComma":
      return 2; // 強制視為第二層
    case "arabicNumber": // 1. 2. 3.
    case "numberedDot":
      return 3; // 強制視為第三層
    case "parenNumbered": // (1) (2) (3)
      return 4; // 強制視為第四層
    default:
      return 3; // 預設值
  }
}

function formatHeadingPrefix(
  level: number | undefined,
  state: HeadingCounterState,
  style?: WordListStyle,
): string {
  // 1. 決定「有效層級 (Effective Level)」
  // 如果有傳入樣式，優先使用樣式對應的層級來計數 (例如選了「一、二、」就強制用 Level 2 計數器)
  // 如果沒有樣式，才退回使用節點原本的 level
  const rawLevel = level || 2;
  const effectiveLevel = style ? getImplicitLevelFromStyle(style) : rawLevel;

  // 2. 針對「有效層級」進行計數 (關鍵修正：這裡不再使用 rawLevel)
  state[effectiveLevel] = (state[effectiveLevel] ?? 0) + 1;

  // 3. 重置所有比「有效層級」更深的計數器
  // 例如：現在數到「五、」(Level 2)，底下的 (1) (Level 4) 必須歸零
  Object.keys(state).forEach((key) => {
    const keyNum = Number(key);
    if (keyNum > effectiveLevel) {
      delete state[keyNum];
    }
  });

  const count = state[effectiveLevel];

  // 4. 根據樣式或層級回傳格式化字串
  if (style) {
    switch (style) {
      case "chineseNumber":
      case "chineseComma":
        return `${formatChineseNumeral(count)}、`;
      case "arabicNumber":
      case "numberedDot":
        return `${count}. `;
      case "parenNumbered":
        return `（${count}）`;
      case "bullet":
        return "";
      default:
        break;
    }
  }

  // Fallback: 如果沒有指定樣式，依據層級給預設格式
  switch (effectiveLevel) {
    case 2:
      return `${formatChineseNumeral(count)}、`;
    case 3:
      return `${count}. `;
    case 4:
      return `（${count}）`;
    default:
      return `${count}. `;
  }
}

function getListBulletLabel(
  style: WordListStyle | undefined,
  index: number,
): string {
  switch (style) {
    case "chineseNumber":
    case "chineseComma":
      return `${formatChineseNumeral(index + 1)}、`;
    case "arabicNumber":
    case "numberedDot":
      return `${index + 1}.`;
    case "parenNumbered":
      return `（${index + 1}）`;
    default:
      return "•";
  }
}

const PARAGRAPH_SUB_HEADING_MAX_LEVEL = 3;

function resolveParagraphEffectiveLevel(node: WordDocumentNode): number {
  if (node.paragraphNumberStyle) {
    return getImplicitLevelFromStyle(node.paragraphNumberStyle);
  }
  return node.level ?? 3;
}

function shouldUseParagraphSubHeadingStyle(node: WordDocumentNode): boolean {
  if (node.type !== "paragraph") return false;
  if (node.paragraphNumbering !== true) return false;
  return (
    resolveParagraphEffectiveLevel(node) <= PARAGRAPH_SUB_HEADING_MAX_LEVEL
  );
}

const formState = ref<WordExportTemplateConfig>({
  documentStyle: { ...DEFAULT_STYLE },
  sectionLayouts: [],
  nodes: [],
});

const versionHistory = computed<WordExportConfigEntry[]>(() => {
  const list = props.template?.word_export_config ?? [];
  return [...list].sort(
    (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime(),
  );
});

// 章節分組接口
interface ChapterGroup {
  id: string;
  title: string;
  nodes: WordDocumentNode[];
  contentNodes: WordDocumentNode[];
  isManual?: boolean; // 是否為手動添加的章節標記
}

// 章節分組邏輯
const groupedNodes = computed<ChapterGroup[]>(() => {
  if (!formState.value.nodes || formState.value.nodes.length === 0) {
    return [];
  }

  const groups: ChapterGroup[] = [];
  let currentChapter: ChapterGroup | null = null;

  const pushCurrentChapter = () => {
    if (currentChapter) {
      groups.push(currentChapter);
    }
  };

  for (const node of formState.value.nodes) {
    const isChapterMarker =
      node.type === "sectionTitle" || node.chapterMarker === true;

    if (isChapterMarker) {
      pushCurrentChapter();
      currentChapter = {
        id: node.id,
        title: node.chapterTitle ?? node.label ?? "未命名章節",
        nodes: [node],
        contentNodes: [],
        isManual: node.chapterMarker === true,
      };
      continue;
    }

    if (!currentChapter) {
      currentChapter = {
        id: `default-${groups.length}`,
        title: "未分組",
        nodes: [],
        contentNodes: [],
        isManual: false,
      };
    }

    currentChapter.nodes.push(node);
    currentChapter.contentNodes.push(node);
  }

  pushCurrentChapter();

  return groups;
});

const selectedChapterId = ref<string>("");

const filteredChapters = computed(() => {
  return groupedNodes.value.filter(
    (group) => group.id === selectedChapterId.value,
  );
});

function getNodeGlobalIndex(nodeId: string): number {
  if (!formState.value.nodes) return -1;
  return formState.value.nodes.findIndex((n) => n.id === nodeId);
}

function getChapterGlobalIndex(chapterId: string): number {
  return groupedNodes.value.findIndex((group) => group.id === chapterId);
}

function moveChapter(chapterId: string, direction: "up" | "down") {
  const allNodes = ensureNodesRoot();
  const currentChapterIndex = getChapterGlobalIndex(chapterId);

  if (direction === "up" && currentChapterIndex <= 0) return;
  if (
    direction === "down" &&
    currentChapterIndex >= groupedNodes.value.length - 1
  )
    return;

  const targetChapterIndex =
    direction === "up" ? currentChapterIndex - 1 : currentChapterIndex + 1;
  const currentChapter = groupedNodes.value[currentChapterIndex];
  const targetChapter = groupedNodes.value[targetChapterIndex];

  if (!currentChapter || !targetChapter) return;

  // 找到章节在所有节点中的范围
  const currentStartIndex = allNodes.findIndex(
    (n) => n.id === currentChapter.nodes[0]?.id,
  );
  const currentEndIndex = currentStartIndex + currentChapter.nodes.length - 1;

  const targetStartIndex = allNodes.findIndex(
    (n) => n.id === targetChapter.nodes[0]?.id,
  );
  const targetEndIndex = targetStartIndex + targetChapter.nodes.length - 1;

  if (currentStartIndex === -1 || targetStartIndex === -1) return;

  // 提取当前章节和目标章节的所有节点
  const currentChapterNodes = allNodes.splice(
    currentStartIndex,
    currentChapter.nodes.length,
  );

  // 计算新的插入位置
  let insertIndex: number;
  if (direction === "up") {
    // 上移：insert before 目标章节
    insertIndex = allNodes.findIndex(
      (n) => n.id === targetChapter.nodes[0]?.id,
    );
  } else {
    // 下移：insert after 目标章节
    const newTargetEndIndex = allNodes.findIndex(
      (n) => n.id === targetChapter.nodes[targetChapter.nodes.length - 1]?.id,
    );
    insertIndex = newTargetEndIndex + 1;
  }

  allNodes.splice(insertIndex, 0, ...currentChapterNodes);
}

function addChapterMarker() {
  const newNode: WordDocumentNode = {
    id: generateNodeId(),
    type: "sectionTitle",
    label: "新章節",
    chapterMarker: true,
    chapterTitle: "新章節",
    level: 1,
  };
  ensureNodesRoot().push(newNode);
}

function addNodeAfterNode(nodeId: string, chapterId: string) {
  const nodes = ensureNodesRoot();
  const chapter = groupedNodes.value.find((group) => group.id === chapterId);
  const chapterNodes = chapter?.contentNodes ?? [];
  const referenceNode = chapterNodes[chapterNodes.length - 1];
  const newNode = createNode({
    type: "paragraph",
    label: "新節點內容",
    level: calculateNodeLevelFromDataPath(""),
    sectionId: referenceNode?.sectionId || props.sections[0]?.id,
    chapterMarker: false,
  });

  const insertAfterIndex = getNodeGlobalIndex(nodeId);
  if (insertAfterIndex === -1) {
    nodes.push(newNode);
    return;
  }

  nodes.splice(insertAfterIndex + 1, 0, newNode);
}

function addNodeToChapter(chapterId: string) {
  const nodes = ensureNodesRoot();
  const chapter = groupedNodes.value.find((group) => group.id === chapterId);
  const chapterNodes = chapter?.nodes ?? [];
  const referenceNode = chapterNodes[chapterNodes.length - 1];
  const newNode = createNode({
    type: "paragraph",
    label: "新節點內容",
    level: calculateNodeLevelFromDataPath(""),
    sectionId: referenceNode?.sectionId || props.sections[0]?.id,
    chapterMarker: false,
  });

  if (!chapter || chapterNodes.length === 0) {
    nodes.push(newNode);
    return;
  }

  const lastNode = chapterNodes[chapterNodes.length - 1];
  if (!lastNode) {
    nodes.push(newNode);
    return;
  }

  const lastIndex = getNodeGlobalIndex(lastNode.id);
  if (lastIndex === -1) {
    nodes.push(newNode);
    return;
  }

  nodes.splice(lastIndex + 1, 0, newNode);
}

function editChapterTitle(chapterId: string) {
  const chapter = groupedNodes.value.find((group) => group.id === chapterId);
  const currentTitle = chapter?.title ?? "";
  const nextTitle = prompt("請輸入章節標題：", currentTitle);
  if (nextTitle === null) return;
  const trimmed = nextTitle.trim();
  if (!trimmed) return;
  updateNode(chapterId, (node) => {
    node.chapterTitle = trimmed;
    node.label = trimmed;
  });
}

function removeChapter(chapterId: string) {
  const chapter = groupedNodes.value.find((group) => group.id === chapterId);
  if (!chapter) return;

  if (!confirm("確定要刪除這個章節嗎？章節下的所有節點也會被刪除。")) {
    return;
  }

  const nodes = ensureNodesRoot();
  const idsToRemove = new Set(chapter.nodes.map((node) => node.id));

  formState.value.nodes = nodes.filter((node) => !idsToRemove.has(node.id));
}

const sectionOptions = computed(() =>
  props.sections.map((section) => ({
    label: section.name,
    value: section.id,
  })),
);

watch(
  () => [props.isVisible, props.template, props.sections],
  ([visible]) => {
    if (visible) {
      hydrateForm(versionHistory.value[0]?.config);
    }
  },
  { immediate: true },
);

watch(
  groupedNodes,
  (groups) => {
    if (!groups.length) {
      selectedChapterId.value = "";
      return;
    }
    if (
      !selectedChapterId.value ||
      !groups.some((group) => group.id === selectedChapterId.value)
    ) {
      const fallback = groups[0];
      if (fallback) {
        selectedChapterId.value = fallback.id;
      }
    }
  },
  { immediate: true },
);

function initializeNodeDefaults(nodes?: WordDocumentNode[]) {
  if (!nodes) return;
  nodes.forEach((node) => {
    if (!node) return;
    if (node.type === "customTable") {
      ensureCustomTableConfig(node);
    }
    if (node.children?.length) {
      initializeNodeDefaults(node.children);
    }
  });
}

function hydrateForm(base?: WordExportTemplateConfig) {
  try {
    const documentStyle = {
      ...DEFAULT_STYLE,
      ...(base?.documentStyle || {}),
    };

    // 使用 JSON 序列化确保数据可用，避免 Vue 响应式代理问题
    const layouts = base?.sectionLayouts
      ? JSON.parse(JSON.stringify(base.sectionLayouts))
      : [];

    const nodes =
      base?.nodes && base.nodes.length > 0
        ? JSON.parse(JSON.stringify(base.nodes))
        : generateDefaultNodes();

    initializeNodeDefaults(nodes);

    formState.value = {
      documentStyle,
      sectionLayouts: layouts,
      nodes,
    };
  } catch (error) {
    console.error("Error hydrating form:", error);
    // 使用默认值
    formState.value = {
      documentStyle: { ...DEFAULT_STYLE },
      sectionLayouts: [],
      nodes: generateDefaultNodes(),
    };
  }
}

function applyVersion(version: WordExportConfigEntry) {
  hydrateForm(version.config);
}

/**
 * Get all top-level data path options for a section
 */
function getDataPathOptions(sectionId: string) {
  const schema = getSectionSchema(sectionId);
  if (!schema) return [];
  return Object.entries(schema).map(([key, meta]) => ({
    value: key,
    label: meta?.title || key,
  }));
}

/**
 * Get nested property options at a specific level
 * Supports cascading dropdown - returns children of the current path
 */
function getNestedPathOptions(
  sectionId: string,
  currentPath: string,
): { value: string; label: string }[] {
  const target = getPropertySchema(sectionId, currentPath);
  if (!target) return [];
  return Object.entries(target).map(([key, meta]) => ({
    value: key,
    label: meta?.title || key,
  }));
}

function getColumnCandidates(sectionId: string, dataPath?: string) {
  const target = getPropertySchema(sectionId, dataPath);
  if (!target) return [];

  const candidates: Array<{ key: string; label: string }> = [];

  const flattenProperties = (
    props: Record<string, SchemaField>,
    prefix = "",
  ) => {
    for (const [key, meta] of Object.entries(props)) {
      const fullKey = prefix ? `${prefix}.${key}` : key;
      const label = meta?.title || key;

      // 只添加叶子节点（非对象、非数组类型的字段）
      if (meta?.type !== "object" && meta?.type !== "array") {
        candidates.push({
          key: fullKey,
          label: prefix ? `${prefix} > ${label}` : label,
        });
      }

      // 如果是物件，递迴展平
      if (meta?.type === "object" && meta?.properties) {
        flattenProperties(meta.properties, fullKey);
      }
    }
  };

  flattenProperties(target);
  return candidates;
}

function getSectionSchema(
  sectionId: string,
): Record<string, SchemaField> | null {
  const section = props.sections.find((item) => item.id === sectionId);
  return section?.json_schema?.properties || null;
}

function getPropertySchema(
  sectionId: string,
  path?: string,
): Record<string, SchemaField> | null {
  const base = getSectionSchema(sectionId);
  if (!base) return null;
  if (!path) return base;

  // Support nested paths with dot notation: "升級轉型動機.升級前後效益比較表"
  const pathParts = path.split(".");
  let current: any = base;

  for (const part of pathParts) {
    if (!current[part]) return null;

    const schema = current[part];
    if (schema.type === "object" && schema.properties) {
      current = schema.properties;
    } else if (schema.type === "array" && schema.items?.properties) {
      current = schema.items.properties;
    } else {
      // Leaf node, cannot drill deeper
      return null;
    }
  }

  return current;
}

function generateNodeId(): string {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `node_${Date.now()}_${Math.random().toString(16).slice(2)}`;
}

/**
 * 生成默认文档节点结构（参考 exportPlanToWordDefault 的逻辑）
 * 为每个 section 生成：
 * 1. 章节标题 (sectionTitle) - level 1
 * 2. 递归处理 schema properties - level 2+
 *    - 对象 → 次标题 (subHeading) + 递归
 *    - 数组of字符串 → 清单 (list) - 根据深度自动选择样式
 *    - 数组of对象 → 表格 (table) - 根据深度自动选择样式
 *    - 简单值 → 段落 (paragraph)
 */
function generateDefaultNodes(): WordDocumentNode[] {
  const nodes: WordDocumentNode[] = [];

  for (const section of props.sections) {
    // 添加章节标题节点（level 1）
    nodes.push({
      id: generateNodeId(),
      label: section.name,
      type: "sectionTitle",
      sectionId: section.id,
      level: 1,
    });

    // 递归处理 schema properties（从 level 2 开始）
    const schemaProps = section.json_schema?.properties;
    if (schemaProps) {
      const childNodes = generateNodesFromSchema(
        section.id,
        schemaProps,
        "",
        2,
      );
      nodes.push(...childNodes);
    }
  }

  return nodes;
}

/**
 * 根据 level 选择列表样式
 * Level 2: 一、二、三、 (chineseNumber)
 * Level 3: 1、2、3、 (arabicNumber)
 * Level 4: （1）、（2）、（3） (parenNumbered)
 * Level 5+: • (bullet)
 */
function getListStyleForLevel(level: number): WordListStyle {
  switch (level) {
    case 2:
      return "chineseNumber";
    case 3:
      return "arabicNumber";
    case 4:
      return "parenNumbered";
    default:
      return "bullet";
  }
}

/**
 * 从 schema properties 递归生成节点
 * 为每个属性创建副标题，然后根据类型创建内容节点
 */
function generateNodesFromSchema(
  sectionId: string,
  properties: Record<string, SchemaField>,
  parentPath: string,
  level: number = 2,
): WordDocumentNode[] {
  const nodes: WordDocumentNode[] = [];

  for (const [key, field] of Object.entries(properties)) {
    const path = parentPath ? `${parentPath}.${key}` : key;
    const label = field.title || key;

    // 为每个属性添加副标题，设置正确的 level
    nodes.push({
      id: generateNodeId(),
      label,
      type: "subHeading",
      sectionId,
      level,
    });

    if (field.type === "array") {
      if (field.items?.properties) {
        // 数组of对象 → 表格，自动展平嵌套对象字段到叶子节点
        const columns: WordTableColumn[] = [];

        const flattenTableColumns = (
          props: Record<string, SchemaField>,
          prefix = "",
        ) => {
          for (const [itemKey, itemField] of Object.entries(props)) {
            const fullKey = prefix ? `${prefix}.${itemKey}` : itemKey;
            const fullLabel = prefix
              ? `${prefix} > ${itemField.title || itemKey}`
              : itemField.title || itemKey;

            // 只添加叶子节点（非对象、非数组类型的字段）
            if (itemField?.type !== "object" && itemField?.type !== "array") {
              columns.push({
                key: fullKey,
                label: fullLabel,
              });
            }

            // 如果嵌套字段是物件，继续展平
            if (itemField?.type === "object" && itemField?.properties) {
              flattenTableColumns(itemField.properties, fullKey);
            }
          }
        };

        flattenTableColumns(field.items.properties);

        nodes.push({
          id: generateNodeId(),
          label: `${label} 表格`,
          type: "table",
          sectionId,
          dataPath: path,
          level: level + 1,
          table: {
            columns,
          },
        });
      } else {
        // 数组of字符串/简单值 → 清单，根据 level 自动选择样式
        nodes.push({
          id: generateNodeId(),
          label: `${label} 清单`,
          type: "list",
          sectionId,
          dataPath: path,
          level: level + 1,
          list: {
            numbering: true,
            style: "chineseNumber",
          },
        });
      }
    } else if (field.type === "object" && field.properties) {
      // 对象 → 递归处理嵌套属性，递增 level
      const nestedNodes = generateNodesFromSchema(
        sectionId,
        field.properties,
        path,
        level + 1,
      );
      nodes.push(...nestedNodes);
    } else {
      // 简单值 → 段落
      nodes.push({
        id: generateNodeId(),
        label: `${label} 内容`,
        type: "paragraph",
        sectionId,
        dataPath: path,
        level: level + 1,
      });
    }
  }

  return nodes;
}

function ensureNodesRoot(): WordDocumentNode[] {
  if (!formState.value.nodes) {
    formState.value.nodes = [];
  }
  return formState.value.nodes;
}

function createNode(
  overrides: Partial<WordDocumentNode> = {},
): WordDocumentNode {
  return {
    id: generateNodeId(),
    label: overrides.label ?? "新節點",
    type: overrides.type ?? "paragraph",
    sectionId: overrides.sectionId ?? props.sections[0]?.id,
    level: overrides.level ?? 1,
    children: overrides.children ?? [],
    ...overrides,
  };
}

function addNode(parentId?: string) {
  const newNode = createNode();
  if (!parentId) {
    ensureNodesRoot().push(newNode);
    return;
  }
  updateNode(parentId, (parent) => {
    if (!parent.children) {
      parent.children = [];
    }
    parent.children.push(newNode);
  });
}

function findNodeReference(
  nodeId: string,
  nodes: WordDocumentNode[] | undefined = formState.value.nodes,
): { node: WordDocumentNode; siblings: WordDocumentNode[] } | null {
  if (!nodes) return null;
  for (const node of nodes) {
    if (node.id === nodeId) {
      return { node, siblings: nodes };
    }
    if (node.children?.length) {
      const found = findNodeReference(nodeId, node.children);
      if (found) {
        return found;
      }
    }
  }
  return null;
}

function updateNode(
  nodeId: string,
  updater: (node: WordDocumentNode) => void,
): void {
  const reference = findNodeReference(nodeId);
  if (!reference) return;
  updater(reference.node);
}

function removeNode(nodeId: string) {
  const reference = findNodeReference(nodeId);
  if (!reference) return;
  const index = reference.siblings.indexOf(reference.node);
  if (index >= 0) {
    reference.siblings.splice(index, 1);
  }
}

function moveNode(nodeId: string, direction: "up" | "down") {
  const reference = findNodeReference(nodeId);
  if (!reference) return;
  const index = reference.siblings.indexOf(reference.node);
  const targetIndex = direction === "up" ? index - 1 : index + 1;
  if (targetIndex < 0 || targetIndex >= reference.siblings.length) return;
  const temp = reference.siblings[targetIndex]!;
  reference.siblings[targetIndex] = reference.node;
  reference.siblings[index] = temp;
}

function handleNodeSectionChange(nodeId: string) {
  updateNode(nodeId, (node) => {
    node.dataPath = "";
    node.level = calculateNodeLevelFromDataPath(node.dataPath);
    if (node.customTable?.cells?.length) {
      node.customTable.cells.forEach((cell) => {
        cell.contents?.forEach((content) => {
          if (content.type === "field") {
            content.dataPath = "";
          }
        });
        ensureCustomTableCellContents(cell);
      });
    }
    handleNodeDataPathChange(nodeId);
  });
}

function handleNodeTypeChange(nodeId: string) {
  updateNode(nodeId, (node) => {
    if (node.type !== "table") {
      delete node.table;
    }
    if (node.type !== "list") {
      delete node.list;
    }
    if (node.type !== "customTable") {
      delete node.customTable;
    } else {
      ensureCustomTableConfig(node);
    }
    if (node.type !== "paragraph") {
      delete node.paragraphNumbering;
      delete node.paragraphNumberStyle;
    }
    if (!shouldShowSectionSelectors(node)) {
      node.sectionId = "";
      node.dataPath = "";
    }
  });
}

function handleNodeDataPathChange(nodeId: string) {
  updateNode(nodeId, (node) => {
    if (node.type === "table" && node.table?.columns?.length) {
      const allow = new Set(
        getNodeColumnCandidates(node).map((option) => option.key),
      );
      node.table.columns = node.table.columns.filter((column) =>
        allow.has(column.key),
      );
    }
    if (node.type === "customTable" && node.customTable?.cells?.length) {
      const allow = new Set(
        getNodeColumnCandidates(node).map((option) => option.key),
      );
      node.customTable.cells.forEach((cell) => {
        let changed = false;
        cell.contents?.forEach((content) => {
          if (
            content.type === "field" &&
            content.dataPath &&
            !allow.has(content.dataPath)
          ) {
            content.dataPath = "";
            changed = true;
          }
        });
        if (changed) {
          ensureCustomTableCellContents(cell);
        }
      });
    }
  });
}

function handleNodeBoldToggle(nodeId: string, value: boolean) {
  updateNode(nodeId, (node) => {
    const style = ensureNodeStyle(node);
    style.bodyBold = value;
  });
}

function handleParagraphNumberingToggle(nodeId: string, value: boolean) {
  updateNode(nodeId, (node) => {
    node.paragraphNumbering = value;
    if (value) {
      node.paragraphNumberStyle = node.paragraphNumberStyle || "arabicNumber";
    } else {
      delete node.paragraphNumberStyle;
    }
  });
}

/**
 * Parse dataPath into path segments
 * Example: "升級轉型動機.升級前後效益比較表" → ["升級轉型動機", "升級前後效益比較表"]
 */
function parseDataPath(dataPath?: string): string[] {
  if (!dataPath) return [];
  return dataPath.split(".").filter((p) => p.length > 0);
}

/**
 * Build dataPath from path segments
 * Example: ["升級轉型動機", "升級前後效益比較表"] → "升級轉型動機.升級前後效益比較表"
 */
function buildDataPath(segments: string[]): string {
  return segments.join(".");
}

/**
 * Get cascading dropdown levels for a node's dataPath
 * Returns array of available options at each nesting level
 */
function getDataPathLevels(
  node: WordDocumentNode,
): Array<{ value: string; label: string }[]> {
  if (!node.sectionId) return [];

  const currentSegments = parseDataPath(node.dataPath);
  const levels: Array<{ value: string; label: string }[]> = [];

  // Level 0: Top-level properties
  levels.push(getDataPathOptions(node.sectionId));

  // Levels 1+: Nested properties based on selected path so far
  for (let i = 0; i < currentSegments.length; i++) {
    const pathSoFar = buildDataPath(currentSegments.slice(0, i + 1));
    const nextLevel = getNestedPathOptions(node.sectionId, pathSoFar);
    if (nextLevel.length === 0) break; // No more nesting possible
    levels.push(nextLevel);
  }

  return levels;
}

/**
 * Check if there are more nesting levels available from current path
 */
function canNestDeeper(node: WordDocumentNode): boolean {
  if (!node.sectionId) return false;
  const currentSegments = parseDataPath(node.dataPath);
  const pathSoFar = node.dataPath || "";
  const nextOptions = getNestedPathOptions(node.sectionId, pathSoFar);
  return nextOptions.length > 0;
}

/**
 * Handle cascading dropdown level change
 */
function calculateNodeLevelFromDataPath(dataPath: string | undefined): number {
  if (!dataPath) return 2;
  const segments = parseDataPath(dataPath);
  // level = 2 + depth of dataPath (starting from level 2 as subheading)
  // e.g., "section" -> level 3, "section.subsection" -> level 4
  return Math.min(2 + segments.length, 5);
}

function handleDataPathLevelChange(
  nodeId: string,
  levelIndex: number,
  value: string,
): void {
  updateNode(nodeId, (node) => {
    const segments = parseDataPath(node.dataPath);

    if (value === "") {
      // Clear this level and all deeper levels
      segments.splice(levelIndex);
    } else {
      // Set this level and clear all deeper levels
      segments[levelIndex] = value;
      segments.splice(levelIndex + 1);
    }

    node.dataPath = buildDataPath(segments);
    node.level = calculateNodeLevelFromDataPath(node.dataPath);
    handleNodeDataPathChange(nodeId);
  });
}

/**
 * Handle adding another nesting level
 */
function handleAddDataPathLevel(nodeId: string): void {
  // Just render another dropdown - the user will select from it
  // The cascading dropdown UI will automatically show the next level
  // when the current path becomes non-empty
}

function getNodeDataPathOptions(node: WordDocumentNode) {
  if (!node.sectionId) return [];
  return getDataPathOptions(node.sectionId);
}

function getNodeColumnCandidates(node: WordDocumentNode) {
  if (!node.sectionId) return [];
  return getColumnCandidates(node.sectionId, node.dataPath);
}

function ensureTableConfig(node: WordDocumentNode) {
  if (!node.table) {
    node.table = { columns: [] };
  }
  if (!node.table.columns) {
    node.table.columns = [];
  }
  if (!node.table.layout) {
    node.table.layout = "auto";
  }
  return node.table;
}

function syncLegacyCustomTableCellFields(cell: WordCustomTableCell) {
  const primary = cell.contents?.[0];
  if (!primary) {
    cell.type = "text";
    cell.text = "";
    cell.dataPath = "";
    return;
  }

  cell.type = primary.type;
  if (primary.type === "text") {
    cell.text = primary.text ?? "";
    cell.dataPath = "";
  } else {
    cell.dataPath = primary.dataPath ?? "";
    cell.text = "";
  }
}

function ensureCustomTableCellContents(cell: WordCustomTableCell) {
  const buildContent = (
    base?: Partial<WordCustomTableCellContent> & {
      type?: WordCustomTableCellContentType;
    },
  ): WordCustomTableCellContent => {
    const resolvedType = base?.type ?? "text";
    return {
      id: base?.id || generateNodeId(),
      type: resolvedType,
      text: resolvedType === "text" ? (base?.text ?? "") : undefined,
      dataPath: resolvedType === "field" ? (base?.dataPath ?? "") : undefined,
    };
  };

  if (!Array.isArray(cell.contents) || cell.contents.length === 0) {
    const fallbackType = cell.type ?? "text";
    cell.contents = [
      buildContent({
        type: fallbackType,
        text: cell.text,
        dataPath: cell.dataPath,
      }),
    ];
  } else {
    cell.contents = cell.contents.map((content) =>
      buildContent({
        id: content.id,
        type: content.type,
        text: content.text,
        dataPath: content.dataPath,
      }),
    );
  }

  syncLegacyCustomTableCellFields(cell);
  return cell.contents;
}

function formatCustomTableFieldValue(value: any): string {
  if (value === null || value === undefined) return "";
  if (Array.isArray(value)) {
    return value
      .map((item) =>
        typeof item === "object" ? JSON.stringify(item) : String(item ?? ""),
      )
      .filter((text) => text.length > 0)
      .join(", ");
  }
  if (typeof value === "object") {
    try {
      return JSON.stringify(value);
    } catch (error) {
      console.warn("Failed to stringify value", error);
      return String(value);
    }
  }
  return String(value);
}

function getCustomTableCellContentValue(
  node: WordDocumentNode,
  sectionData: Record<string, any> | null,
  content: WordCustomTableCellContent,
): string {
  if (!content) return "";
  if (content.type === "text") {
    return content.text ?? "";
  }
  if (!sectionData || !content.dataPath) return "";
  const scopedPath = resolveNodeScopedPath(node, content.dataPath);
  if (!scopedPath) return "";
  const value = getValueByPath(sectionData, scopedPath);
  return formatCustomTableFieldValue(value);
}

function getCustomTableCellDisplayValue(
  node: WordDocumentNode,
  cell: WordCustomTableCell | undefined,
  sectionData: Record<string, any> | null,
): string {
  if (!cell) return "";

  // Read contents without mutating - use existing contents or fallback to legacy fields
  let contents: WordCustomTableCellContent[];
  if (Array.isArray(cell.contents) && cell.contents.length > 0) {
    contents = cell.contents;
  } else {
    contents = [
      {
        id: "",
        type: cell.type ?? "text",
        text: cell.text,
        dataPath: cell.dataPath,
      } as WordCustomTableCellContent,
    ];
  }

  return contents
    .map((content) =>
      getCustomTableCellContentValue(node, sectionData, content),
    )
    .join("");
}

function normalizeCustomTableCells(config: WordCustomTableConfig) {
  const rows = Math.min(Math.max(Math.floor(config.rows || 1), 1), 20);
  const cols = Math.min(Math.max(Math.floor(config.cols || 1), 1), 6);
  const expectedCellCount = rows * cols;
  const existingCells = Array.isArray(config.cells) ? config.cells : [];
  let needsRebuild =
    !Array.isArray(config.cells) || existingCells.length !== expectedCellCount;

  const seenKeys = new Set<string>();
  if (!needsRebuild) {
    for (const cell of existingCells) {
      const rowValid =
        typeof cell.row === "number" && cell.row >= 0 && cell.row < rows;
      const colValid =
        typeof cell.col === "number" && cell.col >= 0 && cell.col < cols;
      if (!rowValid || !colValid) {
        needsRebuild = true;
        break;
      }
      const key = `${cell.row}-${cell.col}`;
      if (seenKeys.has(key)) {
        needsRebuild = true;
        break;
      }
      seenKeys.add(key);
    }
  }

  const finalizeCell = (cell: WordCustomTableCell) => {
    if (!cell.id) {
      cell.id = generateNodeId();
    }
    ensureCustomTableCellContents(cell);
    return cell;
  };

  if (!needsRebuild) {
    existingCells.forEach(finalizeCell);
    config.rows = rows;
    config.cols = cols;
    return;
  }

  const existing = new Map<string, WordCustomTableCell>();
  for (const cell of existingCells) {
    if (
      typeof cell.row !== "number" ||
      typeof cell.col !== "number" ||
      cell.row < 0 ||
      cell.col < 0
    ) {
      continue;
    }
    const key = `${cell.row}-${cell.col}`;
    if (!existing.has(key)) {
      existing.set(key, cell);
    }
  }

  const cells: WordCustomTableCell[] = [];
  for (let row = 0; row < rows; row++) {
    for (let col = 0; col < cols; col++) {
      const key = `${row}-${col}`;
      const cell = existing.get(key) ?? {
        id: generateNodeId(),
        row,
        col,
        type: "text",
        text: "",
        dataPath: "",
      };
      cell.row = row;
      cell.col = col;
      cells.push(finalizeCell(cell));
    }
  }

  config.rows = rows;
  config.cols = cols;
  config.cells = cells;
}

function ensureCustomTableConfig(node: WordDocumentNode) {
  if (!node.customTable) {
    node.customTable = {
      rows: 2,
      cols: 2,
      cells: [],
    };
  }
  normalizeCustomTableCells(node.customTable);
  return node.customTable;
}

function getCustomTableRowCells(node: WordDocumentNode, rowIndex: number) {
  if (!node.customTable?.cells) {
    return [];
  }
  return node.customTable.cells
    .filter((cell) => cell.row === rowIndex)
    .sort((a, b) => a.col - b.col);
}

function ensureListItemConfig(node: WordDocumentNode) {
  const listConfig = ensureListConfig(node);
  if (!listConfig.itemConfig) {
    listConfig.itemConfig = {
      useSubNodes: false,
    };
  }
  return listConfig.itemConfig;
}

function ensureTableFixedLayout(node: WordDocumentNode) {
  const table = ensureTableConfig(node);
  if (!table.fixedLayout) {
    table.fixedLayout = {
      rows: 2,
      cols: 2,
      cells: [],
    };
  }
  return table.fixedLayout;
}

function addListNodeChild(nodeId: string) {
  updateNode(nodeId, (node) => {
    if (!node.children) {
      node.children = [];
    }
    const childNode: WordDocumentNode = {
      id: generateNodeId(),
      type: "paragraph",
      sectionId: node.sectionId,
      level: (node.level || 1) + 1,
    };
    node.children.push(childNode);
  });
}

function handleCustomTableDimensionChange(
  nodeId: string,
  dimension: "rows" | "cols",
  rawValue: number,
) {
  const sanitized = Number.isFinite(rawValue) ? Math.floor(rawValue) : 1;
  updateNode(nodeId, (node) => {
    const customTable = ensureCustomTableConfig(node);
    const clamped =
      dimension === "rows"
        ? Math.min(Math.max(sanitized, 1), 20)
        : Math.min(Math.max(sanitized, 1), 6);
    customTable[dimension] = clamped;
    normalizeCustomTableCells(customTable);
  });
}

function addCustomTableCellContent(
  cell: WordCustomTableCell,
  type: WordCustomTableCellContentType,
) {
  if (!cell.contents) {
    cell.contents = [];
  }
  cell.contents.push({
    id: generateNodeId(),
    type,
    text: type === "text" ? "" : undefined,
    dataPath: type === "field" ? "" : undefined,
  });
  ensureCustomTableCellContents(cell);
}

function removeCustomTableCellContent(
  cell: WordCustomTableCell,
  contentId: string,
) {
  if (!cell.contents || cell.contents.length === 0) {
    cell.contents = [
      {
        id: generateNodeId(),
        type: "text",
        text: "",
      },
    ];
  }
  if (cell.contents.length === 1) {
    const first = cell.contents[0];
    if (first) {
      first.type = "text";
      first.text = "";
      first.dataPath = "";
    }
    syncLegacyCustomTableCellFields(cell);
    return;
  }
  cell.contents = cell.contents.filter((content) => content.id !== contentId);
  if (!cell.contents.length) {
    cell.contents = [
      {
        id: generateNodeId(),
        type: "text",
        text: "",
      },
    ];
  }
  ensureCustomTableCellContents(cell);
}

function moveCustomTableCellContent(
  cell: WordCustomTableCell,
  contentIndex: number,
  direction: "up" | "down",
) {
  if (!cell.contents || cell.contents.length < 2) return;
  const newIndex = direction === "up" ? contentIndex - 1 : contentIndex + 1;
  if (newIndex < 0 || newIndex >= cell.contents.length) return;
  const current = cell.contents[contentIndex];
  const target = cell.contents[newIndex];
  if (!current || !target) return;
  cell.contents[contentIndex] = target;
  cell.contents[newIndex] = current;
  ensureCustomTableCellContents(cell);
}

function handleCustomTableCellContentTypeChange(
  cell: WordCustomTableCell,
  content: WordCustomTableCellContent,
) {
  if (content.type === "text") {
    content.text = content.text ?? "";
    content.dataPath = "";
  } else {
    content.dataPath = content.dataPath ?? "";
    content.text = "";
  }
  ensureCustomTableCellContents(cell);
}

function resolveNodeScopedPath(
  node: WordDocumentNode,
  relativePath?: string,
): string | undefined {
  if (!relativePath || !relativePath.trim()) {
    return node.dataPath;
  }
  if (!node.dataPath || !node.dataPath.trim()) {
    return relativePath;
  }
  const trimmedRelative = relativePath.trim();
  const basePrefix = `${node.dataPath}.`;
  if (trimmedRelative.startsWith(basePrefix)) {
    return trimmedRelative;
  }
  return `${node.dataPath}.${trimmedRelative}`;
}

/**
 * 處理遞歸節點編輯器的事件
 */
function handleRecursiveNodeUpdate(
  nodeId: string,
  updater: (node: WordDocumentNode) => void,
) {
  // 遞歸查找節點（包括子節點）
  const findAndUpdate = (
    nodes: WordDocumentNode[] | undefined,
    targetId: string,
  ): boolean => {
    if (!nodes) return false;
    for (const node of nodes) {
      if (!node) continue;
      if (node.id === targetId) {
        try {
          updater(node);
        } catch (error) {
          console.error("Error updating node:", error);
          throw error;
        }
        return true;
      }
      if (node.children && findAndUpdate(node.children, targetId)) {
        return true;
      }
    }
    return false;
  };

  findAndUpdate(formState.value.nodes, nodeId);
}

function handleRecursiveNodeRemove(nodeId: string) {
  // 遞歸查找並刪除節點（包括子節點）
  const findAndRemove = (
    nodes: WordDocumentNode[] | undefined,
    targetId: string,
  ): boolean => {
    if (!nodes) return false;
    for (let i = 0; i < nodes.length; i++) {
      const currentNode = nodes[i];
      if (!currentNode) continue;
      if (currentNode.id === targetId) {
        nodes.splice(i, 1);
        return true;
      }
      if (
        currentNode.children &&
        findAndRemove(currentNode.children, targetId)
      ) {
        return true;
      }
    }
    return false;
  };

  findAndRemove(formState.value.nodes, nodeId);
}

function handleRecursiveNodeAddChild(nodeId: string) {
  // 遞歸查找節點並添加子節點
  const findAndAddChild = (
    nodes: WordDocumentNode[] | undefined,
    targetId: string,
  ): boolean => {
    if (!nodes) return false;
    for (const node of nodes) {
      if (!node) continue;
      if (node.id === targetId) {
        if (!node.children) {
          node.children = [];
        }
        const childNode: WordDocumentNode = {
          id: generateNodeId(),
          type: "paragraph",
          sectionId: node.sectionId,
          level: (node.level || 1) + 1,
        };
        node.children.push(childNode);
        return true;
      }
      if (node.children && findAndAddChild(node.children, targetId)) {
        return true;
      }
    }
    return false;
  };

  findAndAddChild(formState.value.nodes, nodeId);
}

function addTableCell(nodeId: string) {
  updateNode(nodeId, (node) => {
    const fixedLayout = ensureTableFixedLayout(node);
    fixedLayout.cells.push({
      row: 0,
      col: 0,
      isHeader: false,
    });
  });
}

function removeTableCell(nodeId: string, cellIndex: number) {
  updateNode(nodeId, (node) => {
    if (node.table?.fixedLayout?.cells) {
      node.table.fixedLayout.cells.splice(cellIndex, 1);
    }
  });
}

function ensureListConfig(node: WordDocumentNode) {
  if (!node.list) {
    node.list = {
      numbering: true,
      style: "chineseNumber",
    };
  }
  if (!node.list.style) {
    node.list.style = "chineseNumber";
  }
  return node.list;
}

function ensureNodeStyle(node: WordDocumentNode) {
  if (!node.style) {
    node.style = {};
  }
  return node.style;
}

function toggleNodeColumnForNode(
  nodeId: string,
  option: WordTableColumn,
  checked?: boolean,
) {
  updateNode(nodeId, (node) => {
    const table = ensureTableConfig(node);
    if (checked) {
      if (!table.columns.find((column) => column.key === option.key)) {
        table.columns.push({ ...option });
      }
    } else {
      table.columns = table.columns.filter(
        (column) => column.key !== option.key,
      );
    }
  });
}

function onNodeColumnToggle(
  nodeId: string,
  option: WordTableColumn,
  event: Event,
) {
  const target = event.target as HTMLInputElement | undefined;
  toggleNodeColumnForNode(nodeId, option, target?.checked);
}

function moveTableColumn(
  nodeId: string,
  columnIndex: number,
  direction: "up" | "down",
) {
  const reference = findNodeReference(nodeId);
  if (
    !reference ||
    reference.node.type !== "table" ||
    !reference.node.table?.columns
  )
    return;

  const columns = reference.node.table.columns;
  const newIndex = direction === "up" ? columnIndex - 1 : columnIndex + 1;

  if (newIndex < 0 || newIndex >= columns.length) return;

  const colAtIndex = columns[columnIndex];
  const colAtNewIndex = columns[newIndex];

  if (!colAtIndex || !colAtNewIndex) return;

  // 交換列的位置
  columns[columnIndex] = colAtNewIndex;
  columns[newIndex] = colAtIndex;
}

function shouldShowTemplateInput(node: WordDocumentNode) {
  return node.type === "customText";
}

function shouldShowNodeLabel(node: WordDocumentNode) {
  return !["paragraph", "table", "customTable", "list", "customText"].includes(
    node.type,
  );
}

function shouldShowSectionSelectors(node: WordDocumentNode) {
  return !["sectionTitle", "subHeading", "customText"].includes(node.type);
}

function walkNodes(
  nodes: WordDocumentNode[] | undefined,
  callback: (node: WordDocumentNode) => boolean | void,
): boolean {
  if (!nodes) return false;
  for (const node of nodes) {
    if (!node) continue;
    const shouldStop = callback(node);
    if (shouldStop) {
      return true;
    }
    if (node.children?.length && walkNodes(node.children, callback)) {
      return true;
    }
  }
  return false;
}

function deepClone<T>(value: T): T {
  try {
    // 先尝试 structuredClone（更安全）
    if (typeof structuredClone === "function") {
      return structuredClone(value);
    }
  } catch (error) {
    console.warn("structuredClone failed, falling back to JSON method:", error);
  }

  // 使用 JSON 序列化作为 fallback（这会自动剔除函数和不可序列化的对象）
  try {
    return JSON.parse(JSON.stringify(value));
  } catch (error) {
    console.error("deepClone failed completely:", error);
    // 最后的 fallback：返回原值
    return value;
  }
}

function sanitizeForClone(
  data: WordExportTemplateConfig,
): WordExportTemplateConfig {
  // 创建一个清洁的副本，只包含可序列化的数据
  return {
    documentStyle: {
      headingFont: data.documentStyle?.headingFont,
      headingSizePt: data.documentStyle?.headingSizePt,
      headingBold: data.documentStyle?.headingBold,
      subHeadingFont: data.documentStyle?.subHeadingFont,
      subHeadingSizePt: data.documentStyle?.subHeadingSizePt,
      subHeadingBold: data.documentStyle?.subHeadingBold,
      bodyFont: data.documentStyle?.bodyFont,
      bodySizePt: data.documentStyle?.bodySizePt,
      bodyBold: data.documentStyle?.bodyBold,
    },
    sectionLayouts: data.sectionLayouts
      ? JSON.parse(JSON.stringify(data.sectionLayouts))
      : [],
    nodes: data.nodes ? JSON.parse(JSON.stringify(data.nodes)) : [],
  };
}

function handleSave() {
  try {
    let invalidNodes = false;
    walkNodes(formState.value.nodes, (node) => {
      if (!node) {
        console.warn("Found null/undefined node in node tree");
        return false;
      }
      if (
        node.type === "table" &&
        (!node.table?.columns || !node.table.columns.length)
      ) {
        invalidNodes = true;
        return true;
      }
      return false;
    });

    if (invalidNodes) {
      notifyError("有節點的表格尚未選擇欄位");
      return;
    }

    // 使用 sanitize 函数確保數據可被序列化
    const cleanData = sanitizeForClone(formState.value);
    if (!cleanData || !cleanData.documentStyle) {
      throw new Error("保存數據不完整");
    }

    emit("save", cleanData);
  } catch (error) {
    console.error("Error in handleSave:", error);
    notifyError(
      error instanceof Error ? error.message : "保存失敗，請稍後重試",
    );
  }
}

function formatDate(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString("zh-TW");
}

/**
 * Generate dummy data for a section based on its schema
 */
function generateDummyData(section: SectionRecord): Record<string, any> {
  const schema = section.json_schema?.properties;
  if (!schema) return {};

  const dummy: Record<string, any> = {};

  const generateValueFromSchema = (
    field: SchemaField,
    fieldKey: string,
  ): any => {
    if (field.type === "array") {
      const items = [];
      if (field.items?.properties) {
        // Array of objects
        for (let i = 0; i < 2; i++) {
          const item: Record<string, any> = {};
          for (const [key, itemField] of Object.entries(
            field.items.properties,
          )) {
            item[key] = generateValueFromSchema(itemField, key);
          }
          items.push(item);
        }
      } else {
        // Array of simple values
        items.push(`範例${fieldKey}數據1`, `範例${fieldKey}數據2`);
      }
      return items;
    } else if (field.type === "object" && field.properties) {
      const obj: Record<string, any> = {};
      for (const [key, subField] of Object.entries(field.properties)) {
        obj[key] = generateValueFromSchema(subField, key);
      }
      return obj;
    } else if (
      field.type === "number" ||
      fieldKey.includes("金額") ||
      fieldKey.includes("數量")
    ) {
      return Math.floor(Math.random() * 10000) + 1000;
    } else {
      return `${field.title || fieldKey}的示例內容`;
    }
  };

  for (const [key, field] of Object.entries(schema)) {
    dummy[key] = generateValueFromSchema(field, key);
  }

  return dummy;
}

/**
 * Render a node with dummy data for preview
 */
function renderNodePreview(
  node: WordDocumentNode,
  sectionDataMap: Record<string, Record<string, any>>,
  headingCounters: HeadingCounterState,
): string {
  const indent = 0;

  let html = `<div style="margin-left: ${indent}px; margin-bottom: 12px;">`;

  if (node.type === "sectionTitle") {
    resetHeadingCounters(headingCounters);
    const fontSize = (formState.value.documentStyle.headingSizePt || 18) / 2;
    html += `<h2 style="font-size: ${fontSize}pt; font-weight: bold; margin: 12px 0;">
      ${node.label || "章節標題"}
    </h2>`;
  } else if (node.type === "subHeading") {
    const fontSize = (formState.value.documentStyle.subHeadingSizePt || 14) / 2;
    const showNumbering = node.list?.numbering !== false; // 預設 true
    const prefix = showNumbering
      ? formatHeadingPrefix(node.level, headingCounters, node.list?.style)
      : "";

    html += `<h3 style="font-size: ${fontSize}pt; font-weight: bold; margin: 8px 0;">
      ${prefix}${node.label || "次標題"}
    </h3>`;
  } else if (node.type === "paragraph") {
    const docStyle = formState.value.documentStyle;
    const sectionData = node.sectionId
      ? (sectionDataMap[node.sectionId] ?? null)
      : null;
    const value = sectionData
      ? getValueByPath(sectionData, node.dataPath)
      : `${node.label || "段落內容"} (無資料)`;
    const formattedValue =
      value === undefined || value === null ? "" : String(value);
    const numberingEnabled = node.paragraphNumbering === true;
    const numberingStyle = node.paragraphNumberStyle || "arabicNumber";
    const useSubHeadingTypography = shouldUseParagraphSubHeadingStyle(node);
    const baseFontSizePt = useSubHeadingTypography
      ? docStyle.subHeadingSizePt || 14
      : docStyle.bodySizePt || 12;
    const fontSize = baseFontSizePt / 2;
    const weightValue = useSubHeadingTypography
      ? docStyle.subHeadingBold !== false
      : (node.style?.bodyBold ?? docStyle.bodyBold ?? false);
    const fontWeight = weightValue ? "bold" : "normal";
    const fontFamily = useSubHeadingTypography
      ? docStyle.subHeadingFont || "Times New Roman"
      : docStyle.bodyFont || "Times New Roman";
    const fontFamilyCss = fontFamily.includes(" ")
      ? `'${fontFamily}'`
      : fontFamily;
    const prefix = numberingEnabled
      ? formatHeadingPrefix(node.level ?? 3, headingCounters, numberingStyle)
      : "";
    const labelText = node.label ? `${node.label}: ` : "";
    html += `<p style="font-size: ${fontSize}pt; margin: 6px 0; font-weight: ${fontWeight}; font-family: ${fontFamilyCss};">
      ${prefix}${labelText}${formattedValue}
    </p>`;
  } else if (node.type === "table") {
    const sectionData = node.sectionId ? sectionDataMap[node.sectionId] : null;
    const tableData = sectionData
      ? getValueByPath(sectionData, node.dataPath)
      : [];
    const rows = Array.isArray(tableData) ? tableData : [];
    const columns = node.table?.columns || [];
    const transpose = node.table?.transpose === true;

    html += `<table style="width: 100%; border-collapse: collapse; margin: 8px 0;">`;

    if (!transpose) {
      html += `<thead>
        <tr style="background-color: #f0f0f0;">`;
      for (const col of columns) {
        html += `<th style="border: 1px solid #ccc; padding: 6px;">${col.label}</th>`;
      }
      html += `</tr></thead>`;
    }

    html += `<tbody>`;
    if (transpose) {
      for (const col of columns) {
        html += `<tr><td style="border: 1px solid #ccc; padding: 6px; font-weight: bold;">${col.label}</td>`;
        for (const row of rows) {
          const cellValue =
            typeof row === "object" ? getValueByPath(row, col.key) : row;
          html += `<td style="border: 1px solid #ccc; padding: 6px;">${cellValue}</td>`;
        }
        html += `</tr>`;
      }
    } else {
      for (const row of rows) {
        html += `<tr>`;
        for (const col of columns) {
          const cellValue =
            typeof row === "object" ? getValueByPath(row, col.key) : row;
          html += `<td style="border: 1px solid #ccc; padding: 6px;">${cellValue}</td>`;
        }
        html += `</tr>`;
      }
    }
    html += `</tbody></table>`;
  } else if (node.type === "customTable") {
    const customTable = node.customTable;
    const rows = Math.max(0, customTable?.rows ?? 0);
    const cols = Math.max(0, customTable?.cols ?? 0);
    const bodyFontSize = (formState.value.documentStyle.bodySizePt || 12) / 2;
    const sectionData: Record<string, any> | null = node.sectionId
      ? (sectionDataMap[node.sectionId] ?? null)
      : null;

    if (!rows || !cols || !customTable?.cells?.length) {
      html += `<p style="font-size: ${bodyFontSize}pt; color: #94a3b8; margin: 6px 0;">自訂表格尚未設定內容</p>`;
    } else {
      const cellMap = new Map<string, WordCustomTableCell>();
      for (const cell of customTable.cells) {
        if (!cell) continue;
        cellMap.set(`${cell.row}-${cell.col}`, cell);
      }

      const renderCellValue = (cell?: WordCustomTableCell | null): string =>
        getCustomTableCellDisplayValue(node, cell || undefined, sectionData);

      html += `<table style="width: 100%; border-collapse: collapse; margin: 8px 0;">`;
      for (let rowIndex = 0; rowIndex < rows; rowIndex++) {
        html += "<tr>";
        for (let colIndex = 0; colIndex < cols; colIndex++) {
          const cellKey = `${rowIndex}-${colIndex}`;
          const cell = cellMap.get(cellKey);
          const displayValue = renderCellValue(cell);
          html += `<td style="border: 1px solid #cbd5f5; padding: 6px; font-size: ${bodyFontSize}pt; vertical-align: top;">${
            displayValue || "&nbsp;"
          }</td>`;
        }
        html += "</tr>";
      }
      html += `</table>`;
    }
  } else if (node.type === "list") {
    const sectionData = node.sectionId ? sectionDataMap[node.sectionId] : null;
    const listData = sectionData
      ? getValueByPath(sectionData, node.dataPath)
      : [];
    const items = Array.isArray(listData) ? listData : [listData];

    const isNumbered = node.list?.numbering !== false;
    const listTag = isNumbered ? "ol" : "ul";
    const getBulletText = (index: number) =>
      isNumbered ? getListBulletLabel(node.list?.style, index) : "";

    html += `<${listTag} style="margin: 6px 0; padding-left: 0; list-style: none;">`;

    // 清單內為對象且使用子節點時：依「每個 list item」逐項渲染，每項用 itemDataMap 渲染所有 children（含段落與內層清單），避免把多項用逗號合併或把內層清單壓平
    if (
      node.list?.itemConfig?.useSubNodes &&
      items.length > 0 &&
      typeof items[0] === "object" &&
      items[0] !== null &&
      !Array.isArray(items[0]) &&
      node.children?.length
    ) {
      for (let i = 0; i < items.length; i++) {
        const item = items[i];
        const itemDataMap: Record<string, Record<string, any>> = {};
        const currentSectionId = node.sectionId;
        if (currentSectionId && typeof item === "object" && item !== null) {
          itemDataMap[currentSectionId] = item as Record<string, any>;
        }

        const firstChild = node.children[0];
        let firstChildDisplayHtml = "";

        if (firstChild) {
          let adjustedFirstChild = { ...firstChild };
          if (node.dataPath && firstChild.dataPath) {
            const parentPathPrefix = node.dataPath + ".";
            if (firstChild.dataPath.startsWith(parentPathPrefix)) {
              adjustedFirstChild = {
                ...firstChild,
                dataPath: firstChild.dataPath.substring(
                  parentPathPrefix.length,
                ),
              };
            } else if (firstChild.dataPath.includes(parentPathPrefix)) {
              // 子節點可能是從 section 起的完整路徑（如 執行步驟及方法.細分方法.細分名稱），當前 item 已是 list 項，取「細分方法.」之後的相對路徑
              const after =
                firstChild.dataPath.indexOf(parentPathPrefix) +
                parentPathPrefix.length;
              adjustedFirstChild = {
                ...firstChild,
                dataPath: firstChild.dataPath.substring(after),
              };
            }
          }

          if (adjustedFirstChild.type === "paragraph") {
            const childSectionData = adjustedFirstChild.sectionId
              ? itemDataMap[adjustedFirstChild.sectionId]
              : null;
            const value = childSectionData
              ? getValueByPath(childSectionData, adjustedFirstChild.dataPath)
              : adjustedFirstChild.label || "段落內容";
            const textContent = value == null ? "" : String(value);
            const childBold =
              adjustedFirstChild.style?.bodyBold ??
              formState.value.documentStyle.bodyBold ??
              false;
            const fontWeight = childBold ? "bold" : "normal";
            firstChildDisplayHtml = `<span style="font-weight: ${fontWeight};">${textContent}</span>`;
          }
        }

        const bullet = getBulletText(i);
        const displayFirstChild = firstChildDisplayHtml || "";
        html += `<li style="margin: 4px 0;">${bullet} ${displayFirstChild}`;

        if (node.children.length > 1) {
          html += `<ul style="margin: 6px 0; padding-left: 1.25em; list-style: none;">`;
          for (
            let childIndex = 1;
            childIndex < node.children.length;
            childIndex++
          ) {
            const childNode = node.children[childIndex];
            if (!childNode) continue;
            let adjustedChildNode = { ...childNode };
            if (node.dataPath && childNode.dataPath) {
              const parentPathPrefix = node.dataPath + ".";
              if (childNode.dataPath.startsWith(parentPathPrefix)) {
                adjustedChildNode = {
                  ...childNode,
                  dataPath: childNode.dataPath.substring(
                    parentPathPrefix.length,
                  ),
                };
              } else if (childNode.dataPath.includes(parentPathPrefix)) {
                // 子節點為完整路徑（如 執行步驟及方法.細分方法.說明）時，取 list 項相對路徑
                const after =
                  childNode.dataPath.indexOf(parentPathPrefix) +
                  parentPathPrefix.length;
                adjustedChildNode = {
                  ...childNode,
                  dataPath: childNode.dataPath.substring(after),
                };
              }
            }

            if (adjustedChildNode.type === "paragraph") {
              const childSectionData = adjustedChildNode.sectionId
                ? itemDataMap[adjustedChildNode.sectionId]
                : null;
              const value = childSectionData
                ? getValueByPath(childSectionData, adjustedChildNode.dataPath)
                : adjustedChildNode.label || "段落內容";
              const nestedDisplay =
                value === undefined || value === null ? "" : String(value);
              const childBold =
                adjustedChildNode.style?.bodyBold ??
                formState.value.documentStyle.bodyBold ??
                false;
              const fontWeight = childBold ? "bold" : "normal";
              html += `<li style="margin: 0px 0;"><span style="font-weight: ${fontWeight};">${nestedDisplay}</span></li>`;
            } else {
              const childHtml = renderNodePreview(
                adjustedChildNode,
                itemDataMap,
                headingCounters,
              );
              const innerContent = childHtml.replace(
                /^<div[^>]*>|<\/div>$/g,
                "",
              );
              html += `<li>${innerContent}</li>`;
            }
          }
          html += `</ul>`;
        }

        html += `</li>`;
      }
    } else {
      items.forEach((item, index) => {
        const displayValue =
          typeof item === "object" && item !== null
            ? JSON.stringify(item)
            : String(item ?? "");
        const bullet = getBulletText(index);
        html += `<li style="margin: 4px 0;">${bullet} ${displayValue}</li>`;
      });
    }

    html += `</${listTag}>`;
  } else if (node.type === "customText") {
    const boldSetting =
      node.style?.bodyBold ?? formState.value.documentStyle.bodyBold ?? false;
    const fontWeight = boldSetting ? "bold" : "normal";
    html += `<div style="margin: 6px 0; font-weight: ${fontWeight};">
      ${node.template || "自訂文字"}
    </div>`;
  }

  // 遞歸渲染子節點（適用於所有節點類型，但清單類型的子節點已經在清單項處理中處理過了）
  if (node.children?.length && node.type !== "list") {
    for (const childNode of node.children) {
      html += renderNodePreview(childNode, sectionDataMap, headingCounters);
    }
  }

  html += `</div>`;

  return html;
}

/**
 * Get value from object by dot-notation path
 */
function getValueByPath(obj: Record<string, any>, path?: string): any {
  if (!path || obj == null) return obj;
  const parts = path.split(".").filter((segment) => segment.length > 0);

  const traverse = (current: any, remaining: string[]): any => {
    if (!remaining.length) {
      return current;
    }

    if (Array.isArray(current)) {
      const aggregated: any[] = [];
      current.forEach((item) => {
        const value = traverse(item, remaining);
        if (Array.isArray(value)) {
          aggregated.push(...value);
        } else if (value !== undefined && value !== null) {
          aggregated.push(value);
        }
      });
      return aggregated.length ? aggregated : null;
    }

    if (!current || typeof current !== "object") {
      return null;
    }

    const [segment, ...rest] = remaining;
    if (segment === undefined || !(segment in current)) {
      return null;
    }
    return traverse(current[segment], rest);
  };

  return traverse(obj, parts);
}

/**
 * Generate HTML preview of the document
 */
function generatePreviewHtml(): string {
  // Generate dummy data for all sections
  const sectionDataMap: Record<string, Record<string, any>> = {};
  for (const section of props.sections) {
    sectionDataMap[section.id] = generateDummyData(section);
  }

  const headingCounters = createHeadingCounterState();

  // Render all nodes
  let html = `
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
      <meta charset="UTF-8">
      <title>Word 導出預覽</title>
      <style>
        body {
          font-family: ${formState.value.documentStyle.bodyFont || "Times New Roman"};
          font-size: ${(formState.value.documentStyle.bodySizePt || 12) / 2}pt;
          margin: 40px;
          line-height: 1.6;
          color: #333;
        }
        .preview-container {
          max-width: 900px;
          margin: 0 auto;
          background: white;
          padding: 40px;
          border: 1px solid #eee;
        }
        h2 {
          font-family: ${formState.value.documentStyle.headingFont || "Times New Roman"};
          font-size: ${(formState.value.documentStyle.headingSizePt || 18) / 2}pt;
          font-weight: ${formState.value.documentStyle.headingBold ? "bold" : "normal"};
          margin-top: 20px;
          margin-bottom: 12px;
        }
        h3 {
          font-family: ${formState.value.documentStyle.subHeadingFont || "Times New Roman"};
          font-size: ${(formState.value.documentStyle.subHeadingSizePt || 14) / 2}pt;
          font-weight: ${formState.value.documentStyle.subHeadingBold ? "bold" : "normal"};
          margin-top: 14px;
          margin-bottom: 8px;
        }
        table {
          width: 100%;
          border-collapse: collapse;
          margin: 12px 0;
          font-size: ${(formState.value.documentStyle.bodySizePt || 12) / 2}pt;
        }
        th, td {
          border: 1px solid #999;
          padding: 8px;
          text-align: left;
        }
        th {
          background-color: #e8e8e8;
          font-weight: bold;
        }
        ul, ol {
          margin: 8px 0;
          padding-left: 0;
          list-style-position: inside;
        }
        li {
          margin: 4px 0;
        }
        p {
          margin: 6px 0;
        }
      </style>
    </head>
    <body>
      <div class="preview-container">
  `;

  if (!formState.value.nodes || formState.value.nodes.length === 0) {
    html += "<p style='color: #999;'>尚未設定任何節點。</p>";
  } else {
    for (const node of formState.value.nodes) {
      html += renderNodePreview(node, sectionDataMap, headingCounters);
    }
  }

  html += `
      </div>
    </body>
    </html>
  `;

  return html;
}

// 即時預覽 HTML - 使用防抖避免 iframe 頻繁重載導致滾動位置重置
const debouncedPreviewHtml = ref<string>("");
const previewIframeRef = ref<HTMLIFrameElement | null>(null);
const previewContainerRef = ref<HTMLDivElement | null>(null);

// 防抖計時器
let previewDebounceTimer: NodeJS.Timeout | null = null;

// 保存 iframe 內部的滾動位置
let savedIframeScrollPosition = 0;

// 防抖函數：延遲更新預覽，避免頻繁重新加載 iframe
function updatePreviewWithDebounce() {
  // 清除上一個計時器
  if (previewDebounceTimer) {
    clearTimeout(previewDebounceTimer);
  }

  // 設置新的計時器（800ms 延遲 - 更長的延遲，減少更新頻率）
  previewDebounceTimer = setTimeout(() => {
    try {
      // 保存 iframe 內部的滾動位置
      if (previewIframeRef.value && previewIframeRef.value.contentDocument) {
        const scrollElement =
          previewIframeRef.value.contentDocument.documentElement ||
          previewIframeRef.value.contentDocument.body;
        if (scrollElement) {
          savedIframeScrollPosition = scrollElement.scrollTop;
        }
      }

      // 更新預覽 HTML - 這會導致 iframe 重新加載
      debouncedPreviewHtml.value = generatePreviewHtml();
    } catch (error) {
      console.error("Error generating preview:", error);
    }
  }, 800);
}

// 當 iframe 加載完成時恢復滾動位置
function handleIframeLoad() {
  if (
    previewIframeRef.value &&
    previewIframeRef.value.contentDocument &&
    savedIframeScrollPosition > 0
  ) {
    const scrollElement =
      previewIframeRef.value.contentDocument.documentElement ||
      previewIframeRef.value.contentDocument.body;
    if (scrollElement) {
      nextTick(() => {
        scrollElement.scrollTop = savedIframeScrollPosition;
      });
    }
  }
}

// 監聽 formState 變化，但使用防抖延遲更新
watch(
  () => [formState.value.documentStyle, formState.value.nodes],
  () => {
    updatePreviewWithDebounce();
  },
  { deep: true },
);

// 初始化預覽
onMounted(() => {
  debouncedPreviewHtml.value = generatePreviewHtml();
});

async function handlePreviewExport() {
  try {
    const previewHtml = generatePreviewHtml();

    // Open preview in a new window
    const previewWindow = window.open("", "_blank");
    if (previewWindow) {
      previewWindow.document.write(previewHtml);
      previewWindow.document.close();
    } else {
      notifyError("無法開啟預覽視窗，請檢查瀏覽器設定");
    }
  } catch (err) {
    notifyError(
      `預覽生成失敗: ${err instanceof Error ? err.message : "未知錯誤"}`,
    );
  }
}

/**
 * Build docx Paragraph elements from node
 */
function buildParagraphsFromNode(
  node: WordDocumentNode,
  sectionDataMap: Record<string, Record<string, any>>,
  headingCounters: HeadingCounterState,
): Array<Paragraph | Table> {
  const elements: Array<Paragraph | Table> = [];

  if (node.type === "sectionTitle") {
    resetHeadingCounters(headingCounters);
    elements.push(
      new Paragraph({
        children: [
          new TextRun({
            text: node.label || "章節標題",
            bold: formState.value.documentStyle.headingBold ?? true,
            size: (formState.value.documentStyle.headingSizePt ?? 18) * 2,
            font:
              formState.value.documentStyle.headingFont || "Times New Roman",
          }),
        ],
        spacing: { before: 200, after: 120 },
      }),
    );
  } else if (node.type === "subHeading") {
    // 修改這裡：傳入樣式並檢查開關
    const showNumbering = node.list?.numbering !== false;
    const prefix = showNumbering
      ? formatHeadingPrefix(node.level, headingCounters, node.list?.style)
      : "";

    elements.push(
      new Paragraph({
        children: [
          new TextRun({
            text: `${prefix}${node.label || "次標題"}`,
            bold: formState.value.documentStyle.subHeadingBold ?? true,
            size: (formState.value.documentStyle.subHeadingSizePt ?? 14) * 2,
            font:
              formState.value.documentStyle.subHeadingFont || "Times New Roman",
          }),
        ],
        spacing: { before: 120, after: 80 },
      }),
    );
  } else if (node.type === "paragraph") {
    const sectionData = node.sectionId ? sectionDataMap[node.sectionId] : null;
    const value = sectionData
      ? getValueByPath(sectionData, node.dataPath)
      : `${node.label || "段落內容"} (無資料)`;
    const formattedValue =
      value === undefined || value === null ? "" : String(value);
    const numberingEnabled = node.paragraphNumbering === true;
    const numberingStyle = node.paragraphNumberStyle || "arabicNumber";
    const prefix = numberingEnabled
      ? formatHeadingPrefix(node.level ?? 3, headingCounters, numberingStyle)
      : "";
    const labelText = node.label ? `${node.label}: ` : "";
    const text = `${prefix}${labelText}${formattedValue}`;
    const docStyle = formState.value.documentStyle;
    const useSubHeadingTypography = shouldUseParagraphSubHeadingStyle(node);
    const paragraphBold = useSubHeadingTypography
      ? docStyle.subHeadingBold !== false
      : (node.style?.bodyBold ?? docStyle.bodyBold ?? false);
    const paragraphFont = useSubHeadingTypography
      ? docStyle.subHeadingFont || "Times New Roman"
      : docStyle.bodyFont || "Times New Roman";
    const paragraphSizePt = useSubHeadingTypography
      ? docStyle.subHeadingSizePt || 14
      : docStyle.bodySizePt || 12;

    elements.push(
      new Paragraph({
        children: [
          new TextRun({
            text,
            size: paragraphSizePt * 2,
            font: paragraphFont,
            bold: paragraphBold,
          }),
        ],
        spacing: { after: 60 },
        alignment: node.style?.alignment
          ? getAlignmentType(node.style.alignment)
          : AlignmentType.LEFT,
      }),
    );
  } else if (node.type === "table") {
    const sectionData = node.sectionId ? sectionDataMap[node.sectionId] : null;
    const tableData = sectionData
      ? getValueByPath(sectionData, node.dataPath)
      : [];
    const rows = Array.isArray(tableData) ? tableData : [];
    const columns = node.table?.columns || [];
    const transpose = node.table?.transpose === true;
    const bodySize = (formState.value.documentStyle.bodySizePt ?? 12) * 2;

    if (columns.length > 0) {
      let headerCells: TableCell[];
      let dataRows: TableRow[];

      if (transpose) {
        // 倒置：表頭 = 欄位 + 原資料列序號
        headerCells = [
          new TableCell({
            children: [
              new Paragraph({
                children: [
                  new TextRun({
                    text: "欄位",
                    bold: true,
                    size: bodySize,
                  }),
                ],
              }),
            ],
          }),
          ...rows.map(
            (_, r) =>
              new TableCell({
                children: [
                  new Paragraph({
                    children: [
                      new TextRun({
                        text: String(r + 1),
                        bold: true,
                        size: bodySize,
                      }),
                    ],
                  }),
                ],
              }),
          ),
        ];
        // 倒置：每一列 = 原欄位標題 + 各資料列在該欄位的值
        dataRows = columns.map(
          (col) =>
            new TableRow({
              children: [
                new TableCell({
                  children: [
                    new Paragraph({
                      children: [
                        new TextRun({
                          text: col.label,
                          bold: true,
                          size: bodySize,
                        }),
                      ],
                    }),
                  ],
                }),
                ...rows.map(
                  (row) =>
                    new TableCell({
                      children: [
                        new Paragraph({
                          children: [
                            new TextRun({
                              text: String(
                                typeof row === "object"
                                  ? (getValueByPath(row, col.key) ?? "")
                                  : row,
                              ),
                              size: bodySize,
                            }),
                          ],
                        }),
                      ],
                    }),
                ),
              ],
            }),
        );
      } else {
        headerCells = columns.map(
          (col) =>
            new TableCell({
              children: [
                new Paragraph({
                  children: [
                    new TextRun({
                      text: col.label,
                      bold: true,
                      size: bodySize,
                    }),
                  ],
                }),
              ],
            }),
        );
        dataRows = rows.map(
          (row) =>
            new TableRow({
              children: columns.map(
                (col) =>
                  new TableCell({
                    children: [
                      new Paragraph({
                        children: [
                          new TextRun({
                            text: String(
                              typeof row === "object"
                                ? (getValueByPath(row, col.key) ?? "")
                                : row,
                            ),
                            size: bodySize,
                          }),
                        ],
                      }),
                    ],
                  }),
              ),
            }),
        );
      }

      const tableRows = transpose
        ? dataRows
        : [new TableRow({ children: headerCells }), ...dataRows];

      elements.push(
        new Table({
          rows: tableRows,
          width: { size: 100, type: "pct" },
        }),
      );
    }
  } else if (node.type === "list") {
    const sectionData = node.sectionId ? sectionDataMap[node.sectionId] : null;
    const listData = sectionData
      ? getValueByPath(sectionData, node.dataPath)
      : [];
    const items = Array.isArray(listData) ? listData : [listData];

    // 清單內為對象且使用子節點時：依每個 list item 逐項渲染，每項用 itemDataMap 渲染所有 children（含段落與內層清單）
    if (node.list?.itemConfig?.useSubNodes && items.length > 0) {
      // 使用子节点渲染
      for (let i = 0; i < items.length; i++) {
        const item = items[i];
        const bullet = node.list?.numbering
          ? getListBulletLabel(node.list?.style, i)
          : "•";

        if (
          typeof item === "object" &&
          item !== null &&
          !Array.isArray(item) &&
          node.children?.length
        ) {
          // 創建一個臨時的 sectionDataMap，將當前項目作為數據源
          const itemDataMap: Record<string, Record<string, any>> = {};
          if (node.sectionId) {
            itemDataMap[node.sectionId] = item;
          }

          // 維持子節點原有順序，依序渲染
          let paragraphIndex = 0;
          const adjustedChildren = node.children.map((childNode) => {
            if (!childNode) return childNode;
            if (!node.dataPath || !childNode.dataPath) {
              return childNode;
            }
            const parentPathPrefix = node.dataPath + ".";
            if (childNode.dataPath.startsWith(parentPathPrefix)) {
              return {
                ...childNode,
                dataPath: childNode.dataPath.substring(parentPathPrefix.length),
              };
            }
            if (childNode.dataPath.includes(parentPathPrefix)) {
              // 子節點為完整路徑（如 執行步驟及方法.細分方法.說明）時，取 list 項相對路徑
              const after =
                childNode.dataPath.indexOf(parentPathPrefix) +
                parentPathPrefix.length;
              return {
                ...childNode,
                dataPath: childNode.dataPath.substring(after),
              };
            }
            return childNode;
          });

          adjustedChildren.forEach((childNode) => {
            if (!childNode) return;
            if (childNode.type === "paragraph") {
              const childSectionData = childNode.sectionId
                ? itemDataMap[childNode.sectionId]
                : null;
              let value: any = null;

              if (childSectionData) {
                if (childNode.dataPath && childNode.dataPath.trim()) {
                  value = getValueByPath(childSectionData, childNode.dataPath);
                }
              }

              let displayValue: string;
              if (value === null || value === undefined) {
                displayValue = childNode.label
                  ? `${childNode.label} (無資料)`
                  : "段落內容 (無資料)";
              } else if (typeof value === "object" && !Array.isArray(value)) {
                const keys = Object.keys(value);
                if (keys.length === 0) {
                  displayValue = childNode.label || "空對象";
                } else {
                  displayValue = JSON.stringify(value);
                }
              } else if (Array.isArray(value)) {
                displayValue = value.length > 0 ? value.join(", ") : "空數組";
              } else {
                displayValue = String(value);
              }

              const prefixText = paragraphIndex === 0 ? `${bullet} ` : "";
              paragraphIndex += 1;
              const childBold =
                childNode.style?.bodyBold ??
                formState.value.documentStyle.bodyBold ??
                false;

              elements.push(
                new Paragraph({
                  children: [
                    new TextRun({
                      text: prefixText + displayValue,
                      size:
                        (formState.value.documentStyle.bodySizePt ?? 12) * 2,
                      font:
                        formState.value.documentStyle.bodyFont ||
                        "Times New Roman",
                      bold: childBold,
                    }),
                  ],
                  spacing: { after: 120 },
                  indent: { left: 0 },
                }),
              );
            } else {
              const childElements = buildParagraphsFromNode(
                childNode,
                itemDataMap,
                headingCounters,
              );
              childElements.forEach((element) => {
                if (element instanceof Paragraph) {
                  const paragraph = element as any;
                  paragraph.indent = { left: 720 };
                }
              });
              elements.push(...childElements);
            }
          });
        }
      }
    } else {
      // 簡單渲染
      for (let i = 0; i < items.length; i++) {
        const item = items[i];
        const bullet = node.list?.numbering
          ? getListBulletLabel(node.list?.style, i)
          : "•";
        const displayValue =
          typeof item === "object" && item !== null
            ? JSON.stringify(item)
            : String(item);

        elements.push(
          new Paragraph({
            children: [
              new TextRun({
                text: `${bullet} ${displayValue}`,
                size: (formState.value.documentStyle.bodySizePt ?? 12) * 2,
                font:
                  formState.value.documentStyle.bodyFont || "Times New Roman",
              }),
            ],
            spacing: { after: 40 },
            indent: { left: 0 },
          }),
        );
      }
    }
  } else if (node.type === "customText") {
    const paragraphBold =
      node.style?.bodyBold ?? formState.value.documentStyle.bodyBold ?? false;
    elements.push(
      new Paragraph({
        children: [
          new TextRun({
            text: node.template || "自訂文字",
            size: (formState.value.documentStyle.bodySizePt ?? 12) * 2,
            font: formState.value.documentStyle.bodyFont || "Times New Roman",
            bold: paragraphBold,
          }),
        ],
        spacing: { after: 60 },
      }),
    );
  } else if (node.type === "customTable") {
    const customTable = node.customTable;
    const rows = Math.max(0, customTable?.rows ?? 0);
    const cols = Math.max(0, customTable?.cols ?? 0);
    const sectionData: Record<string, any> | null = node.sectionId
      ? (sectionDataMap[node.sectionId] ?? null)
      : null;

    if (rows > 0 && cols > 0 && customTable?.cells?.length) {
      const cellMap = new Map<string, WordCustomTableCell>();
      for (const cell of customTable.cells) {
        if (!cell) continue;
        cellMap.set(`${cell.row}-${cell.col}`, cell);
      }

      const tableRows: TableRow[] = [];
      for (let rowIndex = 0; rowIndex < rows; rowIndex++) {
        const tableCells: TableCell[] = [];
        for (let colIndex = 0; colIndex < cols; colIndex++) {
          const cellKey = `${rowIndex}-${colIndex}`;
          const cell = cellMap.get(cellKey);
          const displayValue = getCustomTableCellDisplayValue(
            node,
            cell || undefined,
            sectionData,
          );

          tableCells.push(
            new TableCell({
              children: [
                new Paragraph({
                  children: [
                    new TextRun({
                      text: displayValue || "",
                      size:
                        (formState.value.documentStyle.bodySizePt ?? 12) * 2,
                      font:
                        formState.value.documentStyle.bodyFont ||
                        "Times New Roman",
                    }),
                  ],
                }),
              ],
            }),
          );
        }
        tableRows.push(new TableRow({ children: tableCells }));
      }

      elements.push(
        new Table({
          rows: tableRows,
          width: { size: 100, type: "pct" },
        }),
      );
    }
  }

  // 遞歸渲染子節點（list 類型的子節點已在上面處理過）
  if (node.children?.length && node.type !== "list") {
    for (const childNode of node.children) {
      const childElements = buildParagraphsFromNode(
        childNode,
        sectionDataMap,
        headingCounters,
      );
      elements.push(...childElements);
    }
  }

  return elements;
}

/**
 * Convert alignment string to docx AlignmentType
 */
function getAlignmentType(
  alignment?: string,
): (typeof AlignmentType)[keyof typeof AlignmentType] {
  switch (alignment) {
    case "center":
      return AlignmentType.CENTER;
    case "right":
      return AlignmentType.RIGHT;
    case "left":
    default:
      return AlignmentType.LEFT;
  }
}

/**
 * Generate docx document from current form state
 */
async function generateDocxDocument(): Promise<Blob> {
  // Generate dummy data for all sections
  const sectionDataMap: Record<string, Record<string, any>> = {};
  for (const section of props.sections) {
    sectionDataMap[section.id] = generateDummyData(section);
  }

  // Build document body
  const documentElements: Array<Paragraph | Table> = [];
  const headingCounters = createHeadingCounterState();

  if (formState.value.nodes && formState.value.nodes.length > 0) {
    for (const node of formState.value.nodes) {
      const elements = buildParagraphsFromNode(
        node,
        sectionDataMap,
        headingCounters,
      );
      documentElements.push(...elements);
    }
  } else {
    documentElements.push(
      new Paragraph({
        children: [
          new TextRun({
            text: "尚未設定任何節點。",
            size: 12 * 2,
            color: "999999",
          }),
        ],
      }),
    );
  }

  const doc = new Document({
    sections: [
      {
        properties: {
          page: {
            margin: {
              top: convertInchesToTwip(1),
              right: convertInchesToTwip(1),
              bottom: convertInchesToTwip(1),
              left: convertInchesToTwip(1),
            },
          },
        },
        children: documentElements,
      },
    ],
  });

  return await Packer.toBlob(doc);
}

/**
 * Download document as Word file
 */
async function handleDownloadWord() {
  try {
    const blob = await generateDocxDocument();

    // Create download link
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${props.template?.name || "文檔"}_預覽.docx`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  } catch (err) {
    notifyError(`下載失敗: ${err instanceof Error ? err.message : "未知錯誤"}`);
  }
}
</script>
