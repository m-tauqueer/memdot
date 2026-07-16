/** TipTap JSON ↔ MemdotDocument v1 helpers. */

export type MemdotDocument = {
  schema: "memdot-document";
  schemaVersion: 1;
  documentId: string;
  root: {
    type: "doc";
    content: MemdotBlock[];
  };
};

export type MemdotBlock = {
  type: string;
  attrs: { blockId: string; level?: number; src?: string; alt?: string };
  content?: unknown[];
};

function newBlockId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `00000000-0000-7000-8000-${Date.now().toString(16).padStart(12, "0")}`;
}

export function emptyMemdotDocument(documentId: string): MemdotDocument {
  return {
    schema: "memdot-document",
    schemaVersion: 1,
    documentId,
    root: {
      type: "doc",
      content: [
        {
          type: "paragraph",
          attrs: { blockId: newBlockId() },
          content: [],
        },
      ],
    },
  };
}

/** Convert TipTap/ProseMirror JSON into a MemdotDocument envelope. */
export function tipTapToMemdot(
  documentId: string,
  tipTapDoc: { type?: string; content?: unknown[] },
): MemdotDocument {
  const blocks = (tipTapDoc.content ?? []).map((node) => normalizeBlock(node));
  return {
    schema: "memdot-document",
    schemaVersion: 1,
    documentId,
    root: {
      type: "doc",
      content: blocks.length
        ? blocks
        : [{ type: "paragraph", attrs: { blockId: newBlockId() }, content: [] }],
    },
  };
}

function normalizeBlock(node: unknown): MemdotBlock {
  const record = (node && typeof node === "object" ? node : {}) as {
    type?: string;
    attrs?: Record<string, unknown>;
    content?: unknown[];
  };
  const type = record.type || "paragraph";
  const attrs = record.attrs ?? {};
  const blockId =
    typeof attrs.blockId === "string" && attrs.blockId.length > 0 ? attrs.blockId : newBlockId();
  const next: MemdotBlock = {
    type: mapType(type),
    attrs: { blockId },
  };
  if (typeof attrs.level === "number") {
    next.attrs.level = attrs.level;
  }
  if (type === "heading" && next.attrs.level == null) {
    next.attrs.level = 2;
  }
  if (typeof attrs.src === "string") {
    next.attrs.src = attrs.src;
  }
  if (typeof attrs.alt === "string") {
    next.attrs.alt = attrs.alt;
  }
  if (Array.isArray(record.content)) {
    next.content = record.content.map((child) => normalizeInline(child));
  }
  return next;
}

function mapType(type: string): string {
  switch (type) {
    case "bulletList":
    case "orderedList":
    case "listItem":
    case "blockquote":
    case "codeBlock":
    case "horizontalRule":
    case "heading":
    case "paragraph":
    case "image":
      return type;
    default:
      return "unsupported_block";
  }
}

function normalizeInline(node: unknown): unknown {
  if (!node || typeof node !== "object") {
    return node;
  }
  const record = node as { type?: string; attrs?: Record<string, unknown>; content?: unknown[] };
  if (record.type === "text" || record.type === "hardBreak") {
    return node;
  }
  return normalizeBlock(node);
}

export type TipTapJSON = {
  type: string;
  attrs?: Record<string, unknown>;
  content?: TipTapJSON[];
  text?: string;
  marks?: Array<{ type: string; attrs?: Record<string, unknown> }>;
};

/** TipTap-compatible JSON from a MemdotDocument (blockIds preserved as attrs). */
export function memdotToTipTap(doc: MemdotDocument): TipTapJSON {
  return {
    type: "doc",
    content: doc.root.content.map((block) => ({
      type: block.type === "unsupported_block" ? "paragraph" : block.type,
      attrs: {
        ...block.attrs,
      },
      content: (block.content ?? []) as TipTapJSON[],
    })),
  };
}

export function plainTextFromMemdot(doc: MemdotDocument): string {
  const parts: string[] = [];
  const walk = (nodes: unknown[]) => {
    for (const node of nodes) {
      if (!node || typeof node !== "object") {
        continue;
      }
      const record = node as { type?: string; text?: string; content?: unknown[] };
      if (record.type === "text" && record.text) {
        parts.push(record.text);
      }
      if (Array.isArray(record.content)) {
        walk(record.content);
      }
    }
  };
  walk(doc.root.content);
  return parts.join("");
}
