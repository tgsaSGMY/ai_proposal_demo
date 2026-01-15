// ===== 中文数字数组 =====
// 包含中文数字 "一" 到 "十" 的数组
// 用途：在列表或序号中显示中文数字而不是阿拉伯数字
// 示例：chineseNumbers[0] = "一"，chineseNumbers[1] = "二"
export const chineseNumbers = [
  "一",
  "二",
  "三",
  "四",
  "五",
  "六",
  "七",
  "八",
  "九",
  "十",
];

// ===== 获取带括号的数字 =====
/**
 * 根据索引获取带中文括号（）的数字表示
 *
 * 功能：将数字索引转换为带括号的形式用于列表项编号
 *
 * 参数：
 *   - index: 数字的索引位置（0 为第一个数字）
 *
 * 返回值：
 *   - 带括号的数字字符串，例如 "（1）"、"（2）" 等
 *   - 如果索引超过 9，默认返回 "（10）"
 *
 * 示例：
 *   getParenthesizedNumber(0) -> "（1）"
 *   getParenthesizedNumber(5) -> "（6）"
 *   getParenthesizedNumber(15) -> "（10）" (超出范围，使用默认值)
 */
export function getParenthesizedNumber(index: number): string {
  // 定义数字数组（1 到 10）
  const numbers = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"];
  // 根据索引获取数字，如果超出范围则使用最后的数字 "10"
  const number = numbers[index] || "10";
  // 返回带中文括号的数字字符串
  return `（${number}）`;
}
