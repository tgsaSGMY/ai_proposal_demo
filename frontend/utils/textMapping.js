// 通用 map 定義
const MODE_MAP = {
  golden: { label: "黃金範例", class: "bg-yellow-200 text-yellow-900" },
  internal: { label: "生成企劃", class: "bg-green-200 text-green-900" },
  synthetic: { label: "AI生成", class: "bg-sky-200 text-sky-900" },
};

const STATUS_MAP = {
  completed: "text-emerald-600",
  generating_idea: "text-sky-600",
  generating_plan: "text-indigo-600",
  completed_idea: "text-teal-600",
  pending: "text-gray-500",
  error: "text-rose-600",
};

const SOURCE_TYPE_MAP = {
  golden_samples: { label: "黃金樣本", class: "bg-yellow-100 text-yellow-800" },
  synthetic_data: { label: "生成資料", class: "bg-blue-100 text-blue-800" },
  external_direct: { label: "外部資料", class: "bg-green-100 text-green-800" },
};

// 統一輸出函數
export function modeMap(status) {
  return MODE_MAP[status]?.label || "未知";
}

export function getModeTypeClass(type) {
  return MODE_MAP[type]?.class || "bg-gray-200 text-gray-800";
}

export function getStatusTextColor(status) {
  return STATUS_MAP[status] || "text-gray-500";
}

export function getSourceTypeName(type) {
  return SOURCE_TYPE_MAP[type]?.label || type;
}

export function getSourceTypeClass(type) {
  return SOURCE_TYPE_MAP[type]?.class || "bg-gray-100 text-gray-800";
}
