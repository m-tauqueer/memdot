import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "Memdot",
  description: "Memdot application shell (Phase 1 scaffold)",
  applicationName: "Memdot",
  appleWebApp: {
    capable: true,
    title: "Memdot",
  },
};

export const viewport: Viewport = {
  themeColor: "#000000",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
