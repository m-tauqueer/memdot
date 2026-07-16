import { PageHeader } from "@/src/components/shell/PageHeader";
import { SurfaceState } from "@/src/components/states/SurfaceState";

export default function ReviewPage() {
  return (
    <>
      <PageHeader
        eyebrow="Learning"
        title="Review"
        description="Due queue with evidence-backed scheduling. Offline review pack is the only offline learning surface."
      />
      <SurfaceState
        kind="empty"
        title="Nothing due"
        description="Eligible graded attempts feed this queue. Chat and reveals do not raise demonstrated evidence."
      />
    </>
  );
}
