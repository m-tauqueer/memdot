"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Banner, Button, Input } from "@memdot/ui";

import { useSession } from "@/src/components/auth/SessionProvider";
import { RequireAuth } from "@/src/components/shell/RequireAuth";
import { ApiError, attestAdult } from "@/src/lib/api/client";
import { setOnboardingProfile } from "@/src/lib/offline/store";

type Step = "age" | "profile" | "space" | "import";

function OnboardingForm() {
  const router = useRouter();
  const session = useSession();
  const [step, setStep] = useState<Step>("age");
  const [confirmed, setConfirmed] = useState(false);
  const [displayName, setDisplayName] = useState("");
  const [timezone, setTimezone] = useState(
    typeof Intl !== "undefined" ? Intl.DateTimeFormat().resolvedOptions().timeZone : "UTC",
  );
  const [languages, setLanguages] = useState<Array<"en" | "hi" | "hinglish">>(["en"]);
  const [spacePreference, setSpacePreference] = useState<"general" | "learning">("general");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  function toggleLanguage(code: "en" | "hi" | "hinglish") {
    setLanguages((prev) =>
      prev.includes(code) ? prev.filter((item) => item !== code) : [...prev, code],
    );
  }

  async function submitAge() {
    setBusy(true);
    setError(null);
    try {
      await attestAdult(confirmed);
      setStep("profile");
    } catch (err) {
      // Already-active accounts may still proceed through local onboarding prefs.
      if (err instanceof ApiError && (err.status === 400 || err.status === 409)) {
        setStep("profile");
      } else {
        setError(
          err instanceof ApiError
            ? `${err.message}${err.correlationId ? ` (${err.correlationId})` : ""}`
            : "Could not save attestation",
        );
      }
    } finally {
      setBusy(false);
    }
  }

  async function finish() {
    const accountId = session.session?.account_id;
    if (!accountId) {
      setError("Missing account");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await setOnboardingProfile(accountId, {
        displayName: displayName.trim() || "Learner",
        timezone,
        contentLanguages: languages.length ? languages : ["en"],
        spacePreference,
        completedAt: new Date().toISOString(),
      });
      router.replace("/today");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save onboarding");
      setBusy(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-dvh max-w-lg flex-col justify-center px-6 py-10">
      <p className="text-label mb-3">Onboarding</p>
      <Banner
        tone="info"
        title="Public beta"
        description="Experimental features may change. Capacity is not guaranteed forever."
        live="off"
      />

      {step === "age" ? (
        <>
          <h1 className="mt-6 m-0 font-[family-name:var(--font-display)] text-3xl font-semibold tracking-tight">
            Confirm you are 18 or older
          </h1>
          <p className="text-meta mt-3 leading-relaxed">
            V1 is adults-only. Memdot does not ask for a birth date or identity document.
          </p>
          <label className="mt-8 flex items-start gap-3 text-sm">
            <input
              type="checkbox"
              className="mt-1"
              checked={confirmed}
              onChange={(event) => setConfirmed(event.target.checked)}
            />
            <span>I confirm that I am at least 18 years old.</span>
          </label>
          {!confirmed ? (
            <p className="text-meta mt-3">
              If you cannot confirm, you cannot use hosted Memdot. No product content will be stored.
            </p>
          ) : null}
          <div className="mt-6">
            <Button
              label={busy ? "Saving…" : "Continue"}
              disabled={!confirmed || busy}
              onClick={() => void submitAge()}
            />
          </div>
        </>
      ) : null}

      {step === "profile" ? (
        <>
          <h1 className="mt-6 m-0 font-[family-name:var(--font-display)] text-3xl font-semibold tracking-tight">
            Profile defaults
          </h1>
          <p className="text-meta mt-3">UI chrome stays English. Content languages are hints only.</p>
          <div className="mt-6 grid gap-3">
            <Input
              label="Display name"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
            />
            <Input label="Timezone" value={timezone} onChange={(e) => setTimezone(e.target.value)} />
            <fieldset className="m-0 border-0 p-0">
              <legend className="md-label">Content language hints</legend>
              <div className="mt-2 flex flex-wrap gap-3 text-sm">
                {(
                  [
                    ["en", "English"],
                    ["hi", "Hindi"],
                    ["hinglish", "Hinglish"],
                  ] as const
                ).map(([code, label]) => (
                  <label key={code} className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={languages.includes(code)}
                      onChange={() => toggleLanguage(code)}
                    />
                    {label}
                  </label>
                ))}
              </div>
            </fieldset>
            <Button label="Continue" onClick={() => setStep("space")} />
          </div>
        </>
      ) : null}

      {step === "space" ? (
        <>
          <h1 className="mt-6 m-0 font-[family-name:var(--font-display)] text-3xl font-semibold tracking-tight">
            Starting Space
          </h1>
          <p className="text-meta mt-3">
            Prefer a General Space or Learning Space. Course details can wait.
          </p>
          <div className="mt-6 grid gap-3">
            <label className="flex items-start gap-3 rounded-xl border border-border p-3 text-sm">
              <input
                type="radio"
                name="space"
                checked={spacePreference === "general"}
                onChange={() => setSpacePreference("general")}
              />
              <span>
                <strong>General Space</strong>
                <br />
                Capture sources and memory without a course structure.
              </span>
            </label>
            <label className="flex items-start gap-3 rounded-xl border border-border p-3 text-sm">
              <input
                type="radio"
                name="space"
                checked={spacePreference === "learning"}
                onChange={() => setSpacePreference("learning")}
              />
              <span>
                <strong>Learning Space</strong>
                <br />
                You can add course name, term, and syllabus later in Wave 10.
              </span>
            </label>
            <Button label="Continue" onClick={() => setStep("import")} />
          </div>
        </>
      ) : null}

      {step === "import" ? (
        <>
          <h1 className="mt-6 m-0 font-[family-name:var(--font-display)] text-3xl font-semibold tracking-tight">
            Import later
          </h1>
          <p className="text-meta mt-3">
            Initial import and AI connection are optional. You can reach an empty Today without
            uploading or connecting a service.
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Button
              label={busy ? "Finishing…" : "Go to Today"}
              disabled={busy}
              onClick={() => void finish()}
            />
            <Button
              label="Skip for now"
              variant="secondary"
              disabled={busy}
              onClick={() => void finish()}
            />
          </div>
        </>
      ) : null}

      {error ? (
        <p className="mt-4 text-sm text-[color:var(--destructive)]" role="alert">
          {error}
        </p>
      ) : null}
    </main>
  );
}

export default function OnboardingPage() {
  return (
    <RequireAuth>
      <OnboardingForm />
    </RequireAuth>
  );
}
