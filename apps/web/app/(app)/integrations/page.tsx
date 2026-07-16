import { PageHeader } from "@/src/components/shell/PageHeader";

export default function IntegrationsPage() {
  return (
    <>
      <PageHeader
        eyebrow="Connections"
        title="Integrations"
        description="Notion, MCP clients, and model/BYOK settings."
      />
      <div className="grid gap-3 md:grid-cols-3">
        {[
          ["Notion", "Selected inbound pages and approved outbound under a dedicated root."],
          ["MCP clients", "Consent, scopes, revocation, and context receipts."],
          ["Models / BYOK", "Hosted default or bring-your-own key with retention disclosure."],
        ].map(([title, body]) => (
          <section key={title} className="rounded-2xl border border-border bg-card p-4">
            <h2 className="m-0 text-sm font-semibold">{title}</h2>
            <p className="text-meta mt-2 leading-relaxed">{body}</p>
          </section>
        ))}
      </div>
    </>
  );
}
