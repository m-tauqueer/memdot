/**
 * Next.js instrumentation — validate web settings at process startup.
 * Ensures loadWebSettings is not test-only.
 */
export async function register(): Promise<void> {
  const { loadWebSettings } = await import("./lib/settings");
  loadWebSettings(process.env);
}
