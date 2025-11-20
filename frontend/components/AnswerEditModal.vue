<template>
  <Transition name="fade">
    <div
      v-if="visible"
      class="fixed inset-0 bg-black bg-opacity-60 z-50 flex items-center justify-center p-4"
      @click.self="emitCancel"
    >
      <div
        class="w-full max-w-lg bg-white rounded-2xl shadow-2xl p-6 space-y-5 text-slate-900"
      >
        <div class="space-y-1">
          <p class="text-xs uppercase tracking-widest text-indigo-600">
            修改回答
          </p>
          <h3 class="text-lg font-semibold">{{ questionLabel }}</h3>
          <p class="text-sm text-slate-600 whitespace-pre-line">
            {{ questionPrompt }}
          </p>
        </div>
        <textarea
          v-model="draftModel"
          class="w-full h-40 border border-slate-200 rounded-2xl p-3 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          placeholder="請輸入新的回答"
        ></textarea>
        <div class="flex justify-end gap-3">
          <button
            type="button"
            class="px-4 py-2 rounded-full border border-slate-300 text-slate-600 text-sm font-semibold hover:bg-slate-100"
            @click="emitCancel"
          >
            取消
          </button>
          <button
            type="button"
            class="px-5 py-2 rounded-full bg-gradient-to-r from-indigo-600 to-purple-500 text-white text-sm font-semibold disabled:opacity-60"
            @click="emitSave"
          >
            儲存修改
          </button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { computed, toRefs } from "vue";

const props = defineProps({
  visible: { type: Boolean, default: false },
  questionLabel: { type: String, default: "" },
  questionPrompt: { type: String, default: "" },
  draft: { type: String, default: "" },
});

const emit = defineEmits(["update:draft", "cancel", "save"]);

const { visible, questionLabel, questionPrompt } = toRefs(props);

const draftModel = computed({
  get: () => props.draft,
  set: (value: string) => emit("update:draft", value),
});

function emitCancel() {
  emit("cancel");
}

function emitSave() {
  emit("save");
}
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
