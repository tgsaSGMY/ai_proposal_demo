export interface NameRecommendConfig {
  traits: string;
  examples: string[];
}

export const MAX_NAME_RECOMMEND_EXAMPLES = 5;

export function normalizeNameRecommendConfig(
  value?: Partial<NameRecommendConfig> | null,
): NameRecommendConfig {
  const traits = typeof value?.traits === "string" ? value.traits : "";
  const examples = Array.isArray(value?.examples)
    ? value.examples.filter((item): item is string => typeof item === "string")
    : [];

  return {
    traits,
    examples,
  };
}
