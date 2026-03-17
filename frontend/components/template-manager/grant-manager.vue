<!-- 主題管理 -->
<template>
  <section class="bg-white rounded-2xl shadow p-5">
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-lg font-semibold text-slate-900">主題列表</h2>
      <div class="flex gap-2">
        <button
          type="button"
          class="text-xs text-slate-500 underline"
          @click="emit('refresh')"
        >
          重新整理
        </button>
        <button
          type="button"
          class="text-xs bg-slate-900 text-white px-3 py-1.5 rounded-lg font-semibold hover:bg-slate-800"
          @click="emit('new')"
        >
          新增主題
        </button>
      </div>
    </div>
    <div class="overflow-x-auto">
      <table class="min-w-full text-sm">
        <thead>
          <tr class="text-left text-slate-500 border-b">
            <th class="py-2">ID</th>
            <th class="py-2">名稱</th>
            <th class="py-2 text-right">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="grant in grants"
            :key="grant.id"
            class="border-b last:border-b-0"
          >
            <td class="py-2 font-mono text-xs text-slate-600">
              {{ grant.id }}
            </td>
            <td class="py-2 text-slate-800">{{ grant.name }}</td>
            <td class="py-2 text-right">
              <button
                type="button"
                class="text-xs text-indigo-600 font-semibold"
                @click="emit('edit', grant)"
              >
                編輯
              </button>
            </td>
          </tr>
          <tr v-if="!grants.length">
            <td colspan="3" class="py-6 text-center text-slate-400">
              尚無主題資料
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { PropType } from "vue";

// 主題資料的最小結構，保留索引簽名以相容後端擴充欄位。
interface GrantRecord {
  id: string;
  name: string;
  [key: string]: any;
}

// 接收父層提供的主題清單。
const props = defineProps({
  grants: {
    type: Array as PropType<GrantRecord[]>,
    default: () => [],
  },
});

// 對外派發事件：編輯既有主題、新增主題、重新整理列表。
const emit = defineEmits<{
  (e: "edit", grant: GrantRecord): void;
  (e: "new"): void;
  (e: "refresh"): void;
}>();

// 提供元件名稱，方便 Vue DevTools 與錯誤追蹤辨識。
defineOptions({ name: "GrantListSection" });
</script>
