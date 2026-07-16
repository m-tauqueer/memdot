import { PageHeader } from "@/src/components/shell/PageHeader";
import { SurfaceState } from "@/src/components/states/SurfaceState";

export default function MemoryActivityPage() {
  return (
    <>
      <PageHeader
        eyebrow="Memory"
        title="Activity"
        description="Reads, writes, receipts, sync, and deletion history."
      />
      <SurfaceState kind="empty" title="No activity yet" description="Auditable events will list here as you use Memdot." />
    </>
  );
}
