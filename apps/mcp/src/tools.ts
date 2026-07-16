import type { CoreMcpHeaders } from "./core-client.js";
import { CoreMcpClient } from "./core-client.js";
import type { McpSettings } from "./settings.js";

export type OAuthProtectedResourceMetadata = {
  resource: string;
  authorization_servers: string[];
  scopes_supported: string[];
  bearer_methods_supported: string[];
};

export type McpToolDefinition = {
  name: string;
  description: string;
  inputSchema: Record<string, unknown>;
  annotations?: { readOnlyHint?: boolean };
};

export const MCP_TOOLS: McpToolDefinition[] = [
  {
    name: "search",
    description: "Search the eligible non-private account (company-knowledge shape).",
    inputSchema: {
      type: "object",
      properties: { query: { type: "string", minLength: 1, maxLength: 2048 } },
      required: ["query"],
      additionalProperties: false,
    },
    annotations: { readOnlyHint: true },
  },
  {
    name: "fetch",
    description: "Fetch a single item by opaque MCP id.",
    inputSchema: {
      type: "object",
      properties: { id: { type: "string", minLength: 1 } },
      required: ["id"],
      additionalProperties: false,
    },
    annotations: { readOnlyHint: true },
  },
  {
    name: "prepare_context",
    description: "Compile context receipt over eligible non-private evidence.",
    inputSchema: {
      type: "object",
      properties: {
        query: { type: "string" },
        purpose: { type: "string" },
        max_tokens: { type: "integer" },
        max_items: { type: "integer" },
      },
      required: ["query"],
      additionalProperties: false,
    },
    annotations: { readOnlyHint: true },
  },
  {
    name: "propose_memory",
    description: "Create a pending memory proposal (never commits canonical memory).",
    inputSchema: {
      type: "object",
      properties: {
        space_id: { type: "string", format: "uuid" },
        assertion_text: { type: "string" },
        title: { type: "string" },
      },
      required: ["space_id", "assertion_text"],
      additionalProperties: false,
    },
  },
  {
    name: "record_interaction",
    description: "Append explicitly supplied external interaction turns.",
    inputSchema: {
      type: "object",
      properties: {
        space_id: { type: "string", format: "uuid" },
        client_conversation_id: { type: "string" },
        role: { type: "string" },
        content: { type: "string" },
        completeness: {
          type: "string",
          enum: ["single_turn", "partial_thread", "complete_import"],
        },
      },
      required: ["space_id", "client_conversation_id", "role", "content", "completeness"],
      additionalProperties: false,
    },
  },
];

export function buildProtectedResourceMetadata(settings: McpSettings): OAuthProtectedResourceMetadata {
  const resource = settings.MCP_OIDC_AUDIENCE || "memdot-mcp";
  const issuer = settings.MCP_OIDC_ISSUER.trim();
  return {
    resource,
    authorization_servers: issuer ? [issuer] : [],
    scopes_supported: [
      "memdot.memory.read",
      "memdot.memory.propose",
      "memdot.interaction.record",
    ],
    bearer_methods_supported: ["header"],
  };
}

export type ToolCallInput = {
  name: string;
  arguments: Record<string, unknown>;
  accountId: string;
  actorId: string;
  coreBaseUrl: string;
};

export async function invokeTool(input: ToolCallInput): Promise<unknown> {
  const purposeByTool: Record<string, CoreMcpHeaders["purpose"]> = {
    search: "external_read",
    fetch: "external_read",
    prepare_context: "external_read",
    propose_memory: "external_propose",
    record_interaction: "external_interaction",
  };
  const purpose = purposeByTool[input.name];
  if (!purpose) {
    throw new Error(`unknown tool: ${input.name}`);
  }

  const client = new CoreMcpClient(input.coreBaseUrl, {
    accountId: input.accountId,
    actorId: input.actorId,
    purpose,
  });

  switch (input.name) {
    case "search":
      return client.search(String(input.arguments.query ?? ""));
    case "fetch":
      return client.fetch(String(input.arguments.id ?? ""));
    case "prepare_context": {
      const body: {
        query: string;
        purpose?: string;
        max_tokens?: number;
        max_items?: number;
      } = { query: String(input.arguments.query ?? "") };
      if (input.arguments.purpose) {
        body.purpose = String(input.arguments.purpose);
      }
      if (typeof input.arguments.max_tokens === "number") {
        body.max_tokens = input.arguments.max_tokens;
      }
      if (typeof input.arguments.max_items === "number") {
        body.max_items = input.arguments.max_items;
      }
      return client.prepareContext(body);
    }
    case "propose_memory": {
      const body: {
        space_id: string;
        assertion_text: string;
        title?: string;
      } = {
        space_id: String(input.arguments.space_id ?? ""),
        assertion_text: String(input.arguments.assertion_text ?? ""),
      };
      if (input.arguments.title) {
        body.title = String(input.arguments.title);
      }
      return client.proposeMemory(body);
    }
    case "record_interaction":
      return client.recordInteraction({
        space_id: String(input.arguments.space_id ?? ""),
        client_conversation_id: String(input.arguments.client_conversation_id ?? ""),
        role: String(input.arguments.role ?? ""),
        content: String(input.arguments.content ?? ""),
        completeness: String(input.arguments.completeness ?? "single_turn"),
      });
    default:
      throw new Error(`unknown tool: ${input.name}`);
  }
}

export function mcpToolResponse(payload: unknown): {
  structuredContent: unknown;
  content: Array<{ type: "text"; text: string }>;
} {
  return {
    structuredContent: payload,
    content: [{ type: "text", text: JSON.stringify(payload) }],
  };
}
