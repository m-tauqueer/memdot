/** Browser SHA-256 hex digest for upload verification. */

export async function sha256Hex(data: ArrayBuffer): Promise<string> {
  const digest = await crypto.subtle.digest("SHA-256", data);
  return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, "0")).join("");
}

export async function sha256File(file: Blob): Promise<string> {
  return sha256Hex(await file.arrayBuffer());
}
