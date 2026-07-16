/**
 * Client-side workspace index for entities Core cannot list yet.
 * Partitioned by account; cleared on logout with offline store.
 */

export type RegistryKind =
  | "space"
  | "source"
  | "document"
  | "course"
  | "conversation"
  | "proposal"
  | "assessment";

export type RegistryItem = {
  id: string;
  kind: RegistryKind;
  title: string;
  spaceId?: string;
  meta?: string;
  updatedAt: string;
};

const KEY = "memdot.workspace.v1";

type File = Record<string, RegistryItem[]>;

const memory: File = {};

function available(): boolean {
  try {
    return typeof localStorage !== "undefined";
  } catch {
    return false;
  }
}

function read(): File {
  if (!available()) {
    return memory;
  }
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? (JSON.parse(raw) as File) : {};
  } catch {
    return {};
  }
}

function write(file: File): void {
  if (!available()) {
    for (const key of Object.keys(memory)) {
      delete memory[key];
    }
    Object.assign(memory, file);
    return;
  }
  localStorage.setItem(KEY, JSON.stringify(file));
}

export function listRegistry(accountId: string, kind?: RegistryKind): RegistryItem[] {
  const rows = read()[accountId] ?? [];
  const filtered = kind ? rows.filter((row) => row.kind === kind) : rows;
  return [...filtered].sort((a, b) => b.updatedAt.localeCompare(a.updatedAt));
}

export function upsertRegistry(accountId: string, item: RegistryItem): RegistryItem[] {
  const file = read();
  const rows = file[accountId] ?? [];
  file[accountId] = [...rows.filter((row) => !(row.kind === item.kind && row.id === item.id)), item];
  write(file);
  return listRegistry(accountId);
}

export function clearRegistry(accountId: string): void {
  const file = read();
  delete file[accountId];
  write(file);
}

export function rememberSpace(accountId: string, spaceId: string, title = "Space"): void {
  upsertRegistry(accountId, {
    id: spaceId,
    kind: "space",
    title,
    updatedAt: new Date().toISOString(),
  });
}
