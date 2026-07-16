import { beforeEach, describe, expect, it } from "vitest";

import {
  clearAccountOffline,
  listPins,
  memoryOfflineAdapter,
  pinItem,
  setOfflineAdapter,
} from "./store.js";

describe("offline store", () => {
  beforeEach(async () => {
    setOfflineAdapter(memoryOfflineAdapter);
    await memoryOfflineAdapter.clearAll();
  });

  it("partitions pins by account and clears on logout helper", async () => {
    await pinItem("acct-a", {
      id: "doc-1",
      kind: "document",
      title: "Notes",
      revisionId: "rev-1",
      revisionAt: "2026-07-17T00:00:00.000Z",
      payload: "cipher",
      pinnedAt: "2026-07-17T00:00:00.000Z",
    });
    await pinItem("acct-b", {
      id: "doc-2",
      kind: "document",
      title: "Other",
      revisionId: "rev-2",
      revisionAt: "2026-07-17T00:00:00.000Z",
      payload: "cipher",
      pinnedAt: "2026-07-17T00:00:00.000Z",
    });

    expect(await listPins("acct-a")).toHaveLength(1);
    expect(await listPins("acct-b")).toHaveLength(1);

    await clearAccountOffline("acct-a");
    expect(await listPins("acct-a")).toHaveLength(0);
    expect(await listPins("acct-b")).toHaveLength(1);
  });
});
