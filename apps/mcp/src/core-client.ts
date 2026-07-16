/** Thin Core HTTP client for MCP tool delegation via service-auth + bearer. */

import { buildServiceAuthHeaders } from "./service-auth.js";

export type CoreMcpHeaders = {
  accountId: string;
  actorId: string;
  purpose: "external_read" | "external_propose" | "external_interaction";
  scopes: string[];
  clientId: string;
  subject: string;
  authorization: string;
  serviceSecret: string;
  correlationId?: string;
  exp?: number;
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

  private buildHeaders(purpose?: CoreMcpHeaders["purpose"]): Record<string, string> {
    const resolvedPurpose = purpose ?? this.headers.purpose;
    const identity: Parameters<typeof buildServiceAuthHeaders>[1] = {
      accountId: this.headers.accountId,
      actorId: this.headers.actorId,
      purpose: resolvedPurpose,
      scopes: this.headers.scopes,
      clientId: this.headers.clientId,
      subject: this.headers.subject,
      authorization: this.headers.authorization,
    };
    if (this.headers.exp !== undefined) {
      identity.exp = this.headers.exp;
    }
    const serviceHeaders = buildServiceAuthHeaders(this.headers.serviceSecret, identity);
    return {
      "Content-Type": "application/json",
      Authorization: this.headers.authorization,
      ...serviceHeaders,
      ...(this.headers.correlationId ? { "X-Correlation-Id": this.headers.correlationId } : {}),
    };
  }

  async search(query: string): Promise<SearchResult> {
    const response = await fetch(`${this.baseUrl}/api/v1/mcp/search`, {
      method: "POST",
      headers: this.buildHeaders("external_read"),
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
      headers: this.buildHeaders("external_read"),
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
      headers: this.buildHeaders("external_read"),
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
      headers: this.buildHeaders("external_propose"),
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
    idempotency_key?: string;
    occurred_at?: string;
    parent_turn_id?: string;
    context_receipt_id?: string;
    client_turn_id?: string;
  }): Promise<Record<string, unknown>> {
    const response = await fetch(`${this.baseUrl}/api/v1/mcp/record-interaction`, {
      method: "POST",
      headers: this.buildHeaders("external_interaction"),
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      throw new Error(`core record-interaction failed: ${response.status}`);
    }
    return (await response.json()) as Record<string, unknown>;
  }
}
