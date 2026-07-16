import { PageHeader } from "@/src/components/shell/PageHeader";
import { SurfaceState } from "@/src/components/states/SurfaceState";

export default function SpacesPage() {
  return (
    <>
      <PageHeader
        eyebrow="Organization"
        title="Spaces"
        description="General and Learning Spaces. Private Spaces never leave Memdot via MCP."
      />
      <SurfaceState
        kind="empty"
        title="No Spaces listed yet"
        description="A Spaces API will populate this directory. Create your first Space during onboarding or from Settings."
      />
    </>
  );
}
