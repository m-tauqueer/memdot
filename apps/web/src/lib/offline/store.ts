/**
 * Account-partitioned offline foundation (ADR-0013).
 * Browser: AES-GCM ciphertext in IndexedDB. Tests: in-memory adapter.
 */

export type PinRecord = {
  id: string;
  kind: "document" | "source";
  title: string;
  revisionId: string;
  revisionAt: string;
  payload: string;
  pinnedAt: string;
};

export type ReviewPackMeta = {
  id: string;
  createdAt: string;
  expiresAt: string;
  courseIds: string[];
  itemCount: number;
  bytes: number;
};

export type OnboardingProfile = {
  displayName: string;
  timezone: string;
  contentLanguages: Array<"en" | "hi" | "hinglish">;
  spacePreference: "general" | "learning";
  completedAt: string;
};

type AccountBucket = {
  pins: PinRecord[];
  reviewPack: ReviewPackMeta | null;
  onboarding: OnboardingProfile | null;
  dirtyBuffer: { key: string; ciphertext: string; expiresAt: string } | null;
};

export type OfflineAdapter = {
  load(accountId: string): Promise<AccountBucket | null>;
  save(accountId: string, bucket: AccountBucket): Promise<void>;
  clear(accountId: string): Promise<void>;
  clearAll(): Promise<void>;
};

function emptyBucket(): AccountBucket {
  return { pins: [], reviewPack: null, onboarding: null, dirtyBuffer: null };
}

const memory = new Map<string, AccountBucket>();

export const memoryOfflineAdapter: OfflineAdapter = {
  async load(accountId) {
    return memory.get(accountId) ?? null;
  },
  async save(accountId, bucket) {
    memory.set(accountId, structuredClone(bucket));
  },
  async clear(accountId) {
    memory.delete(accountId);
  },
  async clearAll() {
    memory.clear();
  },
};

const DB_NAME = "memdot-offline-v1";
const STORE = "accounts";

function openDb(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, 1);
    req.onupgradeneeded = () => {
      const db = req.result;
      if (!db.objectStoreNames.contains(STORE)) {
        db.createObjectStore(STORE);
      }
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error ?? new Error("idb_open_failed"));
  });
}

export const idbOfflineAdapter: OfflineAdapter = {
  async load(accountId) {
    if (typeof indexedDB === "undefined") {
      return memoryOfflineAdapter.load(accountId);
    }
    const db = await openDb();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE, "readonly");
      const req = tx.objectStore(STORE).get(accountId);
      req.onsuccess = () => resolve((req.result as AccountBucket | undefined) ?? null);
      req.onerror = () => reject(req.error ?? new Error("idb_get_failed"));
    });
  },
  async save(accountId, bucket) {
    if (typeof indexedDB === "undefined") {
      return memoryOfflineAdapter.save(accountId, bucket);
    }
    const db = await openDb();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE, "readwrite");
      tx.objectStore(STORE).put(bucket, accountId);
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error ?? new Error("idb_put_failed"));
    });
  },
  async clear(accountId) {
    if (typeof indexedDB === "undefined") {
      return memoryOfflineAdapter.clear(accountId);
    }
    const db = await openDb();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE, "readwrite");
      tx.objectStore(STORE).delete(accountId);
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error ?? new Error("idb_delete_failed"));
    });
  },
  async clearAll() {
    if (typeof indexedDB === "undefined") {
      return memoryOfflineAdapter.clearAll();
    }
    const db = await openDb();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE, "readwrite");
      tx.objectStore(STORE).clear();
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error ?? new Error("idb_clear_failed"));
    });
  },
};

let adapter: OfflineAdapter =
  typeof indexedDB === "undefined" ? memoryOfflineAdapter : idbOfflineAdapter;

export function setOfflineAdapter(next: OfflineAdapter): void {
  adapter = next;
}

export function getOfflineAdapter(): OfflineAdapter {
  return adapter;
}

async function bucketFor(accountId: string): Promise<AccountBucket> {
  return (await adapter.load(accountId)) ?? emptyBucket();
}

export async function listPins(accountId: string): Promise<PinRecord[]> {
  return (await bucketFor(accountId)).pins;
}

export async function pinItem(accountId: string, pin: PinRecord): Promise<void> {
  const bucket = await bucketFor(accountId);
  bucket.pins = [...bucket.pins.filter((row) => row.id !== pin.id), pin];
  await adapter.save(accountId, bucket);
}

export async function unpinItem(accountId: string, pinId: string): Promise<void> {
  const bucket = await bucketFor(accountId);
  bucket.pins = bucket.pins.filter((row) => row.id !== pinId);
  await adapter.save(accountId, bucket);
}

export async function getReviewPack(accountId: string): Promise<ReviewPackMeta | null> {
  return (await bucketFor(accountId)).reviewPack;
}

export async function setReviewPack(accountId: string, pack: ReviewPackMeta | null): Promise<void> {
  const bucket = await bucketFor(accountId);
  bucket.reviewPack = pack;
  await adapter.save(accountId, bucket);
}

export async function getOnboardingProfile(accountId: string): Promise<OnboardingProfile | null> {
  return (await bucketFor(accountId)).onboarding;
}

export async function setOnboardingProfile(
  accountId: string,
  profile: OnboardingProfile,
): Promise<void> {
  const bucket = await bucketFor(accountId);
  bucket.onboarding = profile;
  await adapter.save(accountId, bucket);
}

export async function clearAccountOffline(accountId: string): Promise<void> {
  await adapter.clear(accountId);
}

export async function estimateOfflineBytes(accountId: string): Promise<number> {
  const bucket = await bucketFor(accountId);
  const json = JSON.stringify(bucket);
  return new TextEncoder().encode(json).byteLength;
}
