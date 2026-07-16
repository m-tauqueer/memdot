import type { ReactNode } from "react";

import { RegisterServiceWorker } from "@/src/components/pwa/RegisterServiceWorker";
import { AppShell } from "@/src/components/shell/AppShell";
import { RequireAuth } from "@/src/components/shell/RequireAuth";

export default function AuthenticatedLayout({ children }: { children: ReactNode }) {
  return (
    <RequireAuth>
      <RegisterServiceWorker />
      <AppShell>{children}</AppShell>
    </RequireAuth>
  );
}
