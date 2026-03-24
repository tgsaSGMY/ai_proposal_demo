<!-- 方案图片生成模态帐组件：可以按照圖片豐富描述或直接生成圖片，也能通過參考圖片優化 -->
<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition duration-300"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition duration-300"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="modelValue"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
        @click="handleBackdropClick"
      >
        <Transition
          enter-active-class="transition duration-300"
          enter-from-class="opacity-0 scale-95"
          enter-to-class="opacity-100 scale-100"
          leave-active-class="transition duration-300"
          leave-from-class="opacity-100 scale-100"
          leave-to-class="opacity-0 scale-95"
        >
          <div
            v-if="modelValue"
            class="w-full max-w-4xl max-h-[90vh] overflow-y-auto rounded-3xl border border-gray-200 bg-gradient-to-br from-white to-gray-50 p-8 shadow-2xl"
            @click.stop
          >
            <!-- Header -->
            <div class="mb-8 flex items-center justify-between">
              <div>
                <h2
                  class="text-3xl font-bold bg-gradient-to-r from-rose-600 to-pink-600 bg-clip-text text-transparent"
                >
                  AI 計畫配圖生成
                </h2>
                <p class="mt-2 text-sm text-gray-500">
                  為您的計畫生成高質量配圖
                </p>
              </div>
              <button
                class="rounded-full p-2 text-gray-400 transition hover:bg-gray-200 hover:text-gray-600"
                @click="closeModal"
                aria-label="關閉"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  class="h-6 w-6"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </div>

            <!-- Content -->
            <div class="space-y-8">
              <!-- Generate Section -->
              <div
                class="space-y-4 rounded-3xl border border-gray-200 bg-white p-6 shadow-sm"
              >
                <div class="flex items-center gap-3">
                  <div
                    class="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-rose-500 to-pink-500 text-white"
                  >
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                      class="h-5 w-5"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        d="M12 4v16m8-8H4"
                      />
                    </svg>
                  </div>
                  <h3 class="text-lg font-semibold text-gray-900">
                    生成新圖片
                  </h3>
                </div>

                <!-- Reference Image Display -->
                <div
                  v-if="referenceImage"
                  class="rounded-2xl border-2 border-blue-300 bg-blue-50 p-4"
                >
                  <div class="flex items-start justify-between gap-4">
                    <div class="flex-1 min-w-0">
                      <p
                        class="text-xs font-semibold text-blue-600 uppercase tracking-wider mb-2"
                      >
                        參考圖片
                      </p>
                      <p
                        class="text-sm text-blue-700 line-clamp-3 leading-relaxed"
                      >
                        {{ referenceImage.placeholder_text }}
                      </p>
                    </div>
                    <div class="flex-shrink-0">
                      <img
                        v-if="
                          referenceImage.signed_url || referenceImage.public_url
                        "
                        :src="
                          referenceImage.signed_url || referenceImage.public_url
                        "
                        :alt="referenceImage.placeholder_text"
                        class="h-24 w-24 rounded-lg object-cover border border-blue-200"
                      />
                    </div>
                  </div>
                  <button
                    class="mt-3 text-xs font-medium text-blue-600 hover:text-blue-700 transition"
                    @click="referenceImage = null"
                  >
                    ✕ 清除參考
                  </button>
                </div>

                <div>
                  <label
                    for="prompt"
                    class="block text-sm font-semibold text-gray-700 mb-3"
                  >
                    圖片描述
                  </label>
                  <textarea
                    id="prompt"
                    v-model="prompt"
                    :disabled="isGenerating || isEnriching"
                    placeholder="例如：現代科技辦公室，玻璃外牆，日光充足，年輕員工協作工作，專業且創新的氛圍"
                    class="w-full rounded-2xl border border-gray-300 bg-white px-4 py-3 text-sm placeholder-gray-400 transition focus:border-rose-500 focus:outline-none focus:ring-2 focus:ring-rose-200 disabled:bg-gray-50 disabled:text-gray-400"
                    rows="4"
                  />
                </div>

                <!-- Buttons Container -->
                <div class="flex gap-3">
                  <!-- Enrich Prompt Button -->
                  <button
                    class="flex-1 flex items-center justify-center gap-2 rounded-2xl border-2 border-amber-300 bg-amber-50 px-6 py-3 text-base font-semibold text-amber-700 transition hover:bg-amber-100 hover:border-amber-400 disabled:opacity-50"
                    @click="enrichPrompt"
                    :disabled="!prompt.trim() || isGenerating || isEnriching"
                    title="按照計畫書內容豐富圖片描述"
                  >
                    <svg
                      v-if="isEnriching"
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                      class="h-5 w-5 animate-spin"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 4.5a10 10 0 0 1-18.8 4.2"
                      />
                    </svg>
                    <svg
                      v-else
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                      class="h-5 w-5"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        d="M13 10V3L4 14h7v7l9-11h-7z"
                      />
                    </svg>
                    <span>{{
                      isEnriching ? "豐富中..." : "按照計畫書修飾描述"
                    }}</span>
                  </button>

                  <!-- Generate Button -->
                  <button
                    class="flex-1 flex items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-rose-500 to-pink-500 px-6 py-3 text-base font-semibold text-white transition hover:from-rose-600 hover:to-pink-600 hover:shadow-lg disabled:from-rose-300 disabled:to-pink-300"
                    @click="handleGenerate"
                    :disabled="!prompt.trim() || isGenerating || isEnriching"
                  >
                    <svg
                      v-if="isGenerating"
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                      class="h-5 w-5 animate-spin"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 4.5a10 10 0 0 1-18.8 4.2"
                      />
                    </svg>
                    <svg
                      v-else
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                      class="h-5 w-5"
                    >
                      <rect x="3" y="3" width="18" height="18" rx="2" />
                      <circle cx="8.5" cy="8.5" r="1.5" />
                      <path d="M21 15l-5-5L5 21" />
                    </svg>
                    <span>{{ generateBtnText }}</span>
                  </button>
                </div>
              </div>

              <!-- History Section -->
              <div v-if="images.length > 0" class="space-y-4">
                <div class="flex items-center gap-3">
                  <div
                    class="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-amber-500 to-orange-500 text-white"
                  >
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                      class="h-5 w-5"
                    >
                      <circle cx="12" cy="12" r="1" />
                      <path d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div>
                    <h3 class="text-lg font-semibold text-gray-900">
                      過去生成的圖片
                    </h3>
                    <p class="text-xs text-gray-500">
                      共 {{ images.length }} 張
                    </p>
                  </div>
                </div>

                <div class="space-y-3">
                  <div
                    v-for="image in images"
                    :key="image.id"
                    class="group flex gap-4 rounded-2xl border border-gray-200 bg-white p-4 transition hover:border-rose-300 hover:shadow-md"
                  >
                    <!-- Left: Prompt -->
                    <div class="flex-1 min-w-0 flex flex-col justify-between">
                      <div>
                        <p
                          class="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2"
                        >
                          生成提示詞
                        </p>
                        <p
                          class="text-sm text-gray-700 line-clamp-4 leading-relaxed"
                        >
                          {{ image.placeholder_text }}
                        </p>
                      </div>
                      <div class="mt-3 flex items-center gap-2">
                        <button
                          class="inline-flex items-center gap-1 rounded-lg bg-indigo-50 px-3 py-1.5 text-xs font-medium text-indigo-600 transition hover:bg-indigo-100"
                          @click="adjustImage(image)"
                          title="使用此圖片作為參考進行微調"
                        >
                          <svg
                            xmlns="http://www.w3.org/2000/svg"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            stroke-width="2"
                            class="h-3.5 w-3.5"
                          >
                            <path
                              stroke-linecap="round"
                              stroke-linejoin="round"
                              d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                            />
                          </svg>
                          微調
                        </button>
                        <button
                          class="inline-flex items-center gap-1 rounded-lg bg-gray-100 px-3 py-1.5 text-xs font-medium text-gray-700 transition hover:bg-gray-200"
                          @click="copyPrompt(image.placeholder_text)"
                        >
                          <svg
                            xmlns="http://www.w3.org/2000/svg"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            stroke-width="2"
                            class="h-3.5 w-3.5"
                          >
                            <path
                              d="M16 4h2a2 2 0 012 2v14a2 2 0 01-2 2H6a2 2 0 01-2-2V6a2 2 0 012-2h2"
                            />
                            <rect
                              x="8"
                              y="2"
                              width="8"
                              height="4"
                              rx="1"
                              ry="1"
                            />
                          </svg>
                          複製
                        </button>
                        <button
                          class="ml-auto inline-flex items-center gap-1 rounded-lg bg-red-50 px-3 py-1.5 text-xs font-medium text-red-600 transition hover:bg-red-100"
                          @click="handleDeleteImage(image.id)"
                          aria-label="刪除圖片"
                        >
                          <svg
                            xmlns="http://www.w3.org/2000/svg"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            stroke-width="2"
                            class="h-3.5 w-3.5"
                          >
                            <path
                              stroke-linecap="round"
                              stroke-linejoin="round"
                              d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                            />
                          </svg>
                          刪除
                        </button>
                      </div>
                    </div>

                    <!-- Right: Image -->
                    <div class="flex-shrink-0 flex flex-col gap-2">
                      <div
                        class="h-32 w-40 rounded-xl overflow-hidden bg-gray-100 border border-gray-200 cursor-pointer transition hover:shadow-lg hover:border-rose-300 group"
                        @click="selectedImage = image"
                      >
                        <img
                          v-if="image.signed_url || image.public_url"
                          :src="image.signed_url || image.public_url"
                          :alt="image.placeholder_text"
                          class="h-full w-full object-cover group-hover:scale-105 transition"
                        />
                        <div
                          v-else
                          class="h-full w-full flex items-center justify-center text-gray-400"
                        >
                          <svg
                            xmlns="http://www.w3.org/2000/svg"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            stroke-width="1.5"
                            class="h-8 w-8"
                          >
                            <rect x="3" y="3" width="18" height="18" rx="2" />
                            <circle cx="8.5" cy="8.5" r="1.5" />
                            <path d="M21 15l-5-5L5 21" />
                          </svg>
                        </div>
                      </div>
                      <!-- Download Button -->
                      <button
                        v-if="image.signed_url || image.public_url"
                        class="w-full inline-flex items-center justify-center gap-1 rounded-lg bg-blue-50 px-2 py-1.5 text-xs font-medium text-blue-600 transition hover:bg-blue-100"
                        @click="downloadImage(image)"
                        title="下載圖片"
                      >
                        <svg
                          xmlns="http://www.w3.org/2000/svg"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          stroke-width="2"
                          class="h-3.5 w-3.5"
                        >
                          <path
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                          />
                        </svg>
                        下載
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Empty State -->
              <div
                v-else-if="!isLoadingImages"
                class="rounded-3xl border-2 border-dashed border-gray-300 bg-gray-50 p-12 text-center"
              >
                <div
                  class="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-gray-200 to-gray-300"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="1.5"
                    class="h-8 w-8 text-gray-500"
                  >
                    <rect x="3" y="3" width="18" height="18" rx="2" />
                    <circle cx="8.5" cy="8.5" r="1.5" />
                    <path d="M21 15l-5-5L5 21" />
                  </svg>
                </div>
                <p class="text-base font-semibold text-gray-900">
                  還沒有生成過圖片
                </p>
                <p class="mt-2 text-sm text-gray-500">
                  輸入描述並點擊「生成圖片」開始
                </p>
              </div>

              <!-- Loading State -->
              <div
                v-if="isLoadingImages"
                class="flex items-center justify-center py-12"
              >
                <div class="text-center">
                  <div class="mx-auto mb-4 inline-block">
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                      class="h-8 w-8 animate-spin text-rose-500"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 4.5a10 10 0 0 1-18.8 4.2"
                      />
                    </svg>
                  </div>
                  <p class="text-sm font-semibold text-gray-900">
                    正在載入圖片
                  </p>
                  <p class="mt-1 text-xs text-gray-500">請稍候片刻...</p>
                </div>
              </div>
            </div>

            <!-- Footer -->
            <div class="mt-8 flex gap-3 pt-6 border-t border-gray-200">
              <button
                class="flex-1 rounded-2xl border-2 border-gray-300 px-6 py-3 text-sm font-semibold text-gray-700 transition hover:bg-gray-100"
                @click="closeModal"
                :disabled="isGenerating || isEnriching"
              >
                關閉
              </button>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>

  <!-- Image Preview Modal -->
  <Teleport to="body">
    <Transition
      enter-active-class="transition duration-300"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition duration-300"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="selectedImage"
        class="fixed inset-0 z-[60] flex items-center justify-center bg-black/80 backdrop-blur-sm"
        @click="selectedImage = null"
      >
        <Transition
          enter-active-class="transition duration-300"
          enter-from-class="opacity-0 scale-90"
          enter-to-class="opacity-100 scale-100"
          leave-active-class="transition duration-300"
          leave-from-class="opacity-100 scale-100"
          leave-to-class="opacity-0 scale-90"
        >
          <div
            v-if="selectedImage"
            class="relative max-w-4xl max-h-[90vh] flex flex-col bg-white rounded-2xl shadow-2xl overflow-hidden"
            @click.stop
          >
            <!-- Image Container -->
            <div
              class="relative flex-1 overflow-auto bg-gray-900 flex items-center justify-center"
            >
              <img
                :src="selectedImage.signed_url || selectedImage.public_url"
                :alt="selectedImage.placeholder_text"
                class="max-h-full max-w-full object-contain"
              />
            </div>

            <!-- Info Section -->
            <div class="border-t border-gray-200 bg-white p-6">
              <p
                class="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2"
              >
                生成提示詞
              </p>
              <p class="text-base text-gray-700 leading-relaxed mb-4">
                {{ selectedImage.placeholder_text }}
              </p>
            </div>

            <!-- Actions -->
            <div class="flex gap-3 px-6 pb-6 border-t border-gray-200">
              <button
                class="flex-1 inline-flex items-center justify-center gap-2 rounded-lg bg-gray-100 px-4 py-2.5 text-sm font-medium text-gray-700 transition hover:bg-gray-200"
                @click="copyPrompt(selectedImage.placeholder_text)"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  class="h-4 w-4"
                >
                  <path
                    d="M16 4h2a2 2 0 012 2v14a2 2 0 01-2 2H6a2 2 0 01-2-2V6a2 2 0 012-2h2"
                  />
                  <rect x="8" y="2" width="8" height="4" rx="1" ry="1" />
                </svg>
                複製提示詞
              </button>
              <button
                class="flex-1 inline-flex items-center justify-center gap-2 rounded-lg bg-blue-500 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-blue-600"
                @click="
                  downloadImage(selectedImage);
                  selectedImage = null;
                "
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  class="h-4 w-4"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                  />
                </svg>
                下載圖片
              </button>
              <button
                class="flex-1 inline-flex items-center justify-center gap-2 rounded-lg bg-gray-100 px-4 py-2.5 text-sm font-medium text-gray-700 transition hover:bg-gray-200"
                @click="selectedImage = null"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  class="h-4 w-4"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
                關閉
              </button>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from "vue";
import { authenticatedFetch } from "~/composables/useAppAuth";
import { useNotifications } from "~/composables/useNotifications";

interface ImageRecord {
  id: string;
  project_id: string;
  placeholder_text: string;
  storage_path: string;
  public_url: string;
  signed_url?: string;
}

interface Props {
  modelValue: boolean;
  projectId?: string;
}

interface Emits {
  (e: "update:modelValue", value: boolean): void;
  (e: "close"): void;
  (e: "generate", prompt: string): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

const prompt = ref("");
const isGenerating = ref(false);
const generateBtnText = ref("立即生成圖片");
let humorousTimeout: any = null;
const isEnriching = ref(false);
const isLoadingImages = ref(false);
const images = ref<ImageRecord[]>([]);
const selectedImage = ref<ImageRecord | null>(null);
const referenceImage = ref<ImageRecord | null>(null);
const { success, error: notifyError } = useNotifications();
const config = useRuntimeConfig();
const API_BASE_URL = `${config.public.apiBaseUrl}/api`;

// 监听modalValue打开/关闭，打开时加载图片列表
watch(
  () => props.modelValue,
  (isOpen) => {
    if (isOpen && props.projectId) {
      fetchImages();
    } else if (!isOpen) {
      // 关闭时清空参考图片
      referenceImage.value = null;
    }
  },
  { immediate: true },
);

// 从后端API获取项目的图片列表
async function fetchImages() {
  if (!props.projectId) return;

  isLoadingImages.value = true;
  try {
    // 呼叫後端 API 而不是直接查詢 Supabase
    const response = await authenticatedFetch(
      `${API_BASE_URL}/images?project_id=${props.projectId}`,
      {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      },
    );

    if (!response.ok) {
      const detail = await response.text();
      throw new Error(detail || "Failed to load images");
    }

    const data: ImageRecord[] = await response.json();

    images.value = data || [];
  } catch (error: any) {
    console.error("Failed to fetch images", error);
    notifyError(error?.message || "載入圖片失敗");
  } finally {
    isLoadingImages.value = false;
  }
}

// 关闭模态框并重置所有状态
function closeModal() {
  prompt.value = "";
  // 关闭时清空参考图片
  referenceImage.value = null;
  emit("update:modelValue", false);
  emit("close");
}

// 处理背景点击事件，关闭模态框
function handleBackdropClick() {
  closeModal();
}

// 调用后端API生成图片，支持参考图片配置
async function handleGenerate() {
  if (!prompt.value.trim() || !props.projectId) return;

  isGenerating.value = true;
  generateBtnText.value = "生成中...";

  if (humorousTimeout) clearTimeout(humorousTimeout);
  humorousTimeout = setTimeout(() => {
    if (isGenerating.value) {
      generateBtnText.value =
        "稍等片刻，目前系統用量較大，AI 正在瘋狂畫圖中... 🎨💨";
    }
  }, 15000);

  try {
    // 調用後端 API 生成圖片
    const response = await authenticatedFetch(
      `${API_BASE_URL}/images/generate`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          project_id: props.projectId,
          prompt: prompt.value,
          ...(referenceImage.value && {
            reference_image_id: referenceImage.value.id,
            reference_prompt: referenceImage.value.placeholder_text,
          }),
        }),
      },
    );

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || "圖片生成失敗");
    }

    const data = await response.json();
    success("圖片生成成功");
    prompt.value = "";
    referenceImage.value = null;

    // 重新載入圖片列表
    await fetchImages();

    // 發出事件供外部使用
    emit("generate", prompt.value);
  } catch (error: any) {
    console.error("Failed to generate image", error);
    notifyError(error?.message || "圖片生成失敗，請稍後再試");
  } finally {
    isGenerating.value = false;
    generateBtnText.value = "立即生成圖片";
    if (humorousTimeout) {
      clearTimeout(humorousTimeout);
      humorousTimeout = null;
    }
  }
}

// 调用后端API删除指定的图片记录
async function handleDeleteImage(imageId: string) {
  try {
    // 呼叫後端 API 刪除圖片
    const response = await authenticatedFetch(
      `${API_BASE_URL}/images/${imageId}`,
      {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
        },
      },
    );

    if (!response.ok) {
      const detail = await response.text();
      throw new Error(detail || "Failed to delete image");
    }

    images.value = images.value.filter((img) => img.id !== imageId);
    success("圖片已刪除");
  } catch (error: any) {
    console.error("Failed to delete image", error);
    notifyError(error?.message || "刪除圖片失敗");
  }
}

// 将提示词复制到剪贴板
function copyPrompt(text: string) {
  navigator.clipboard
    .writeText(text)
    .then(() => {
      success("提示詞已複製到剪貼板");
    })
    .catch(() => {
      notifyError("複製失敗");
    });
}

// 根据計畫内容丰富提示词
async function enrichPrompt() {
  if (!prompt.value.trim() || !props.projectId) return;

  isEnriching.value = true;
  try {
    const response = await authenticatedFetch(
      `${API_BASE_URL}/images/enrich-prompt`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          project_id: props.projectId,
          prompt: prompt.value,
        }),
      },
    );

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || "豐富描述失敗");
    }

    const data = await response.json();
    prompt.value = data.enriched_prompt;
    success("描述已根據計畫書內容豐富");
  } catch (error: any) {
    console.error("Failed to enrich prompt", error);
    notifyError(error?.message || "豐富描述失敗，請稍後再試");
  } finally {
    isEnriching.value = false;
  }
}

// 下载图片到本地设备
async function downloadImage(image: ImageRecord) {
  try {
    const imageUrl = image.signed_url || image.public_url;
    if (!imageUrl) {
      throw new Error("圖片 URL 不可用");
    }

    const response = await fetch(imageUrl);
    if (!response.ok) {
      throw new Error("下載圖片失敗");
    }

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `image-${Date.now()}.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
    success("圖片下載成功");
  } catch (error: any) {
    console.error("Failed to download image", error);
    notifyError(error?.message || "下載圖片失敗");
  }
}

// 选择图片作为参考，用于后续生成相似风格的图片
function adjustImage(image: ImageRecord) {
  referenceImage.value = image;
  // 滾動到最上方
  window.scrollTo({ top: 0, behavior: "smooth" });
}
</script>
