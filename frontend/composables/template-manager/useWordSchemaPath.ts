import type { WordDocumentNode } from "~/types/wordExport";

export interface SchemaField {
  title?: string;
  type?: string;
  properties?: Record<string, SchemaField>;
  items?: {
    properties?: Record<string, SchemaField>;
  };
}

export interface SchemaSectionRecord {
  id: string;
  json_schema?: {
    properties?: Record<string, SchemaField>;
  } | null;
}

export function parseDataPath(dataPath?: string): string[] {
  if (!dataPath) return [];
  return dataPath.split(".").filter((segment) => segment.length > 0);
}

export function buildDataPath(segments: string[]): string {
  return segments.join(".");
}

export function createWordSchemaPathHelpers(
  getSections: () => SchemaSectionRecord[],
) {
  function getSectionSchema(
    sectionId: string,
  ): Record<string, SchemaField> | null {
    const section = getSections().find((item) => item.id === sectionId);
    return section?.json_schema?.properties || null;
  }

  function getPropertySchema(
    sectionId: string,
    path?: string,
  ): Record<string, SchemaField> | null {
    const base = getSectionSchema(sectionId);
    if (!base) return null;
    if (!path) return base;

    const pathParts = path.split(".");
    let current: Record<string, SchemaField> = base;

    for (const part of pathParts) {
      const schema = current[part];
      if (!schema) return null;

      if (schema.type === "object" && schema.properties) {
        current = schema.properties;
      } else if (schema.type === "array" && schema.items?.properties) {
        current = schema.items.properties;
      } else {
        return null;
      }
    }

    return current;
  }

  function getDataPathOptions(sectionId: string) {
    const schema = getSectionSchema(sectionId);
    if (!schema) return [];
    return Object.entries(schema).map(([key, meta]) => ({
      value: key,
      label: meta?.title || key,
    }));
  }

  function getNestedPathOptions(sectionId: string, currentPath: string) {
    const target = getPropertySchema(sectionId, currentPath);
    if (!target) return [];
    return Object.entries(target).map(([key, meta]) => ({
      value: key,
      label: meta?.title || key,
    }));
  }

  function getDataPathLevels(
    node: Pick<WordDocumentNode, "sectionId" | "dataPath">,
  ): Array<{ value: string; label: string }[]> {
    if (!node.sectionId) return [];

    const currentSegments = parseDataPath(node.dataPath);
    const levels: Array<{ value: string; label: string }[]> = [];

    levels.push(getDataPathOptions(node.sectionId));

    for (let i = 0; i < currentSegments.length; i++) {
      const pathSoFar = buildDataPath(currentSegments.slice(0, i + 1));
      const nextLevel = getNestedPathOptions(node.sectionId, pathSoFar);
      if (nextLevel.length === 0) break;
      levels.push(nextLevel);
    }

    return levels;
  }

  function canNestDeeper(
    node: Pick<WordDocumentNode, "sectionId" | "dataPath">,
  ): boolean {
    if (!node.sectionId) return false;
    const pathSoFar = node.dataPath || "";
    const nextOptions = getNestedPathOptions(node.sectionId, pathSoFar);
    return nextOptions.length > 0;
  }

  function getColumnCandidates(sectionId: string, dataPath?: string) {
    const target = getPropertySchema(sectionId, dataPath);
    if (!target) return [];

    const candidates: Array<{ key: string; label: string }> = [];

    const flattenProperties = (
      properties: Record<string, SchemaField>,
      prefix = "",
    ) => {
      for (const [key, meta] of Object.entries(properties)) {
        const fullKey = prefix ? `${prefix}.${key}` : key;
        const label = meta?.title || key;

        if (meta?.type !== "object" && meta?.type !== "array") {
          candidates.push({
            key: fullKey,
            label: prefix ? `${prefix} > ${label}` : label,
          });
        }

        if (meta?.type === "object" && meta?.properties) {
          flattenProperties(meta.properties, fullKey);
        }
      }
    };

    flattenProperties(target);
    return candidates;
  }

  function isValidDataPath(
    sectionId: string,
    path?: string,
  ): boolean {
    const base = getSectionSchema(sectionId);
    if (!base) return false;
    if (!path) return true; // empty path means the whole section

    const pathParts = path.split(".");
    let current: Record<string, SchemaField> = base;

    for (let i = 0; i < pathParts.length; i++) {
      const part = pathParts[i];
      const schema = current[part];
      if (!schema) return false;

      // If this is the last part, we found it, so it's valid
      if (i === pathParts.length - 1) return true;

      // Otherwise, we need to dig deeper
      if (schema.type === "object" && schema.properties) {
        current = schema.properties;
      } else if (schema.type === "array" && schema.items?.properties) {
        current = schema.items.properties;
      } else {
        return false; // Can't dig deeper
      }
    }

    return true;
  }

  return {
    getSectionSchema,
    getPropertySchema,
    getDataPathOptions,
    getNestedPathOptions,
    getDataPathLevels,
    canNestDeeper,
    getColumnCandidates,
    isValidDataPath,
  };
}
