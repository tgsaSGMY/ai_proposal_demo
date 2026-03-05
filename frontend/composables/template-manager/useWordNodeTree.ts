import type { WordDocumentNode } from "~/types/wordExport";

export type WordNodeDirection = "up" | "down";

export interface WordNodeReference {
  node: WordDocumentNode;
  siblings: WordDocumentNode[];
}

export function findNodeReference(
  nodes: WordDocumentNode[] | undefined,
  nodeId: string,
): WordNodeReference | null {
  if (!nodes) return null;

  for (const node of nodes) {
    if (!node) continue;
    if (node.id === nodeId) {
      return { node, siblings: nodes };
    }
    if (node.children?.length) {
      const found = findNodeReference(node.children, nodeId);
      if (found) {
        return found;
      }
    }
  }

  return null;
}

export function updateNodeById(
  nodes: WordDocumentNode[] | undefined,
  nodeId: string,
  updater: (node: WordDocumentNode) => void,
): boolean {
  const reference = findNodeReference(nodes, nodeId);
  if (!reference) return false;
  updater(reference.node);
  return true;
}

export function removeNodeById(
  nodes: WordDocumentNode[] | undefined,
  nodeId: string,
): boolean {
  if (!nodes) return false;

  for (let index = 0; index < nodes.length; index++) {
    const currentNode = nodes[index];
    if (!currentNode) continue;

    if (currentNode.id === nodeId) {
      nodes.splice(index, 1);
      return true;
    }

    if (removeNodeById(currentNode.children, nodeId)) {
      return true;
    }
  }

  return false;
}

export function moveNodeById(
  nodes: WordDocumentNode[] | undefined,
  nodeId: string,
  direction: WordNodeDirection,
): boolean {
  const reference = findNodeReference(nodes, nodeId);
  if (!reference) return false;

  const currentIndex = reference.siblings.indexOf(reference.node);
  if (currentIndex === -1) return false;

  const targetIndex = direction === "up" ? currentIndex - 1 : currentIndex + 1;
  if (targetIndex < 0 || targetIndex >= reference.siblings.length) {
    return false;
  }

  const swap = reference.siblings[targetIndex];
  if (!swap) return false;

  reference.siblings[targetIndex] = reference.node;
  reference.siblings[currentIndex] = swap;
  return true;
}

export function addChildNodeById(
  nodes: WordDocumentNode[] | undefined,
  nodeId: string,
  createChild: (parent: WordDocumentNode) => WordDocumentNode,
): boolean {
  return updateNodeById(nodes, nodeId, (parent) => {
    if (!parent.children) {
      parent.children = [];
    }
    parent.children.push(createChild(parent));
  });
}

export function walkWordNodes(
  nodes: WordDocumentNode[] | undefined,
  callback: (node: WordDocumentNode) => boolean | void,
): boolean {
  if (!nodes) return false;

  for (const node of nodes) {
    if (!node) continue;
    if (callback(node)) {
      return true;
    }
    if (node.children?.length && walkWordNodes(node.children, callback)) {
      return true;
    }
  }

  return false;
}
