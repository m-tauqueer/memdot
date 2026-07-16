import { PageHeader } from "@/src/components/shell/PageHeader";
import { SurfaceState } from "@/src/components/states/SurfaceState";

export default async function SpaceDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return (
    <>
      <PageHeader eyebrow="Space" title="Space overview" description={`Space ${id}`} />
      <SurfaceState
        kind="partial"
        description="General or Learning overview, map, and scoped sources will attach here."
      />
    </>
  );
}
