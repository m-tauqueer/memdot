"use client";

import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

type ConnectivityValue = {
  online: boolean;
  swUpdateReady: boolean;
  applySwUpdate: () => void;
};

const ConnectivityContext = createContext<ConnectivityValue | null>(null);

export function ConnectivityProvider({ children }: { children: ReactNode }) {
  const [online, setOnline] = useState(
    typeof navigator === "undefined" ? true : navigator.onLine,
  );
  const [swUpdateReady, setSwUpdateReady] = useState(false);
  const [waitingWorker, setWaitingWorker] = useState<ServiceWorker | null>(null);

  useEffect(() => {
    const onOnline = () => setOnline(true);
    const onOffline = () => setOnline(false);
    window.addEventListener("online", onOnline);
    window.addEventListener("offline", onOffline);
    return () => {
      window.removeEventListener("online", onOnline);
      window.removeEventListener("offline", onOffline);
    };
  }, []);

  useEffect(() => {
    const onMessage = (event: MessageEvent) => {
      if (event.data?.type === "MEMDOT_SW_UPDATE_READY" && event.source instanceof ServiceWorker) {
        setWaitingWorker(event.source);
        setSwUpdateReady(true);
      }
    };
    navigator.serviceWorker?.addEventListener("message", onMessage);
    return () => navigator.serviceWorker?.removeEventListener("message", onMessage);
  }, []);

  const value = useMemo<ConnectivityValue>(
    () => ({
      online,
      swUpdateReady,
      applySwUpdate: () => {
        waitingWorker?.postMessage({ type: "MEMDOT_SKIP_WAITING" });
        setSwUpdateReady(false);
        window.location.reload();
      },
    }),
    [online, swUpdateReady, waitingWorker],
  );

  return <ConnectivityContext.Provider value={value}>{children}</ConnectivityContext.Provider>;
}

export function useConnectivity(): ConnectivityValue {
  const ctx = useContext(ConnectivityContext);
  if (!ctx) {
    throw new Error("useConnectivity must be used within ConnectivityProvider");
  }
  return ctx;
}
