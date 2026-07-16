import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Memdot",
    short_name: "Memdot",
    description: "Personal memory with provenance and learning evidence.",
    start_url: "/today",
    display: "standalone",
    background_color: "#f7f6f4",
    theme_color: "#e85d2a",
    icons: [
      {
        src: "/icon.svg",
        sizes: "any",
        type: "image/svg+xml",
        purpose: "any",
      },
    ],
  };
}
