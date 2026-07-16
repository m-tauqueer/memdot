import type { Metadata, Viewport } from "next";
import { DM_Sans, Fraunces } from "next/font/google";
import type { ReactNode } from "react";

import { Providers } from "@/src/components/Providers";

import "./globals.css";

const dmSans = DM_Sans({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});

const fraunces = Fraunces({
  subsets: ["latin"],
  variable: "--font-display",
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "Memdot",
    template: "%s · Memdot",
  },
  description: "Personal memory with provenance, learning evidence, and portable AI access.",
  applicationName: "Memdot",
  appleWebApp: {
    capable: true,
    title: "Memdot",
  },
};

export const viewport: Viewport = {
  themeColor: "#e85d2a",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className={`${dmSans.variable} ${fraunces.variable}`}>
      <body className="font-sans antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
