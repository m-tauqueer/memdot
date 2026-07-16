/** Thin Core HTTP client for MCP tool delegation. */

export type CoreMcpHeaders = {
  accountId: string;
  actorId: string;
  purpose: "external_read" | "external_propose" | "external_interaction";
  correlationId?: string;
};

export type SearchResult = {
  results: Array<{ id: string; title: string; url: string }>;
};

export type FetchResult = {
  id: string;
  title: string;
  text: string;
  url: string;
  metadata?: Record<string, unknown>;
};

export class CoreMcpClient {
  constructor(
    private readonly baseUrl: string,
    private readonly headers: CoreMcpHeaders,
  ) {}

  private buildHeaders(): Record<string, string> {
    return {
      "Content-Type": "application/json",
      "X-Memdot-Account-Id": this.headers.accountId,
      "X-Memdot-Actor-Id": this.headers.actorId,
      "X-Memdot-Purpose": this.headers.purpose,
      ...(this.headers.correlationId
        ? { "X-Correlation-Id": this.headers.correlationId }
        : {}),
    };
  }

  async search(query: string): Promise<SearchResult> {
    const response = await fetch(`${this.baseUrl}/api/v1/mcp/search`, {
      method: "POST",
      headers: this.buildHeaders(),
      body: JSON.stringify({ query }),
    });
    if (!response.ok) {
      throw new Error(`core search failed: ${response.status}`);
    }
    return (await response.json()) as SearchResult;
  }

  async fetch(id: string): Promise<FetchResult> {
    const response = await fetch(`${this.baseUrl}/api/v1/mcp/fetch`, {
      method: "POST",
      headers: this.buildHeaders(),
      body: JSON.stringify({ id }),
    });
    if (!response.ok) {
      throw new Error(`core fetch failed: ${response.status}`);
    }
    return (await response.json()) as FetchResult;
  }

  async prepareContext(body: {
    query: string;
    purpose?: string;
    max_tokens?: number;
    max_items?: number;
  }): Promise<Record<string, unknown>> {
    const response = await fetch(`${this.baseUrl}/api/v1/mcp/prepare-context`, {
      method: "POST",
      headers: this.buildHeaders(),
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      throw new Error(`core prepare-context failed: ${response.status}`);
    }
    return (await response.json()) as Record<string, unknown>;
  }

  async proposeMemory(body: {
    space_id: string;
    assertion_text: string;
    title?: string;
  }): Promise<Record<string, unknown>> {
    const response = await fetch(`${this.baseUrl}/api/v1/mcp/propose-memory`, {
      method: "POST",
      headers: {
        ...this.buildHeaders(),
        "X-Memdot-Purpose": "external_propose",
      },
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      throw new Error(`core propose-memory failed: ${response.status}`);
    }
    return (await response.json()) as Record<string, unknown>;
  }

  async recordInteraction(body: {
    space_id: string;
    client_conversation_id: string;
    role: string;
    content: string;
    completeness: string;
  }): Promise<Record<string, unknown>> {
    const response = await fetch(`${this.baseUrl}/api/v1/mcp/record-interaction`, {
      method: "POST",
      headers: {
        ...this.buildHeaders(),
        "X-Memdot-Purpose": "external_interaction",
      },
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      throw new Error(`core record-interaction failed: ${response.status}`);
    }
    return (await response.json()) as Record<string, unknown>;
  }
}
