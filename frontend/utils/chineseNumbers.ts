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

export function getParenthesizedNumber(index: number): string {
  const numbers = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"];
  const number = numbers[index] || "10";
  return `（${number}）`;
}
