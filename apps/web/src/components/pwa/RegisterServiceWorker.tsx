"use client";

import { useEffect } from "react";

export function RegisterServiceWorker() {
  useEffect(() => {
    if (!("serviceWorker" in navigator)) {
      return;
    }
    const env = process.env.NODE_ENV;
    if (env !== "production") {
      return;
    }
    void navigator.serviceWorker.register("/sw.js").catch(() => {
      /* fail closed — shell still works online */
    });
  }, []);
  return null;
}
