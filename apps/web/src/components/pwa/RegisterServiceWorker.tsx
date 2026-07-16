"use client";

import { useEffect } from "react";

export function RegisterServiceWorker() {
  useEffect(() => {
    if (!("serviceWorker" in navigator)) {
      return;
    }
    // Register in production builds; also allow explicit opt-in for local PWA smoke.
    const allow =
      process.env.NODE_ENV === "production" || process.env.NEXT_PUBLIC_WEB_ENABLE_SW === "1";
    if (!allow) {
      return;
    }
    void navigator.serviceWorker
      .register("/sw.js")
      .then((registration) => {
        if (registration.waiting) {
          registration.waiting.postMessage({ type: "MEMDOT_PING" });
          navigator.serviceWorker.controller?.postMessage({ type: "MEMDOT_CLIENT_READY" });
        }
        registration.addEventListener("updatefound", () => {
          const worker = registration.installing;
          worker?.addEventListener("statechange", () => {
            if (worker.state === "installed" && navigator.serviceWorker.controller) {
              worker.postMessage({ type: "MEMDOT_NOTIFY_UPDATE" });
              navigator.serviceWorker.controller.postMessage({ type: "MEMDOT_SW_UPDATE_READY" });
              // Clients also listen for MEMDOT_SW_UPDATE_READY from the worker install handler.
            }
          });
        });
      })
      .catch(() => {
        /* fail closed — shell still works online */
      });
  }, []);
  return null;
}
