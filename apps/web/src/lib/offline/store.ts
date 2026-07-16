/**
 * Offline state boundary (ADR-0013).
 *
 * Core does not yet issue an encrypted, account-authorized pin or review-pack
 * envelope. Persisting source content in IndexedDB would therefore be an
 * unencrypted local copy with no safe key lifecycle. Until that contract exists,
 * this module is intentionally memory-only: its data disappears on reload and
 * is cleared on logout/account switch.
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

type AccountBucket = {
  pins: PinRecord[];
  reviewPack: ReviewPackMeta | null;
};

export type OfflineAdapter = {
  load(accountId: string): Promise<AccountBucket | null>;
  save(accountId: string, bucket: AccountBucket): Promise<void>;
  clear(accountId: string): Promise<void>;
  clearAll(): Promise<void>;
};

function emptyBucket(): AccountBucket {
  return { pins: [], reviewPack: null };
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

let adapter: OfflineAdapter = memoryOfflineAdapter;

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

/** Reserved for a future Core-authorized encrypted review-pack contract. */
export async function setReviewPack(accountId: string, pack: ReviewPackMeta | null): Promise<void> {
  const bucket = await bucketFor(accountId);
  bucket.reviewPack = pack;
  await adapter.save(accountId, bucket);
}

export async function clearAccountOffline(accountId: string): Promise<void> {
  await adapter.clear(accountId);
}

export async function estimateOfflineBytes(accountId: string): Promise<number> {
  const bucket = await bucketFor(accountId);
  return new TextEncoder().encode(JSON.stringify(bucket)).byteLength;
}
