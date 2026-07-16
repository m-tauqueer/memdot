import type { ReactNode } from "react";

export function PageHeader({
  eyebrow,
  title,
  description,
  actions,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  actions?: ReactNode;
}) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
      <div>
        {eyebrow ? <p className="text-label mb-1">{eyebrow}</p> : null}
        <h1 className="m-0 font-[family-name:var(--font-display)] text-3xl font-semibold tracking-tight">
          {title}
        </h1>
        {description ? <p className="text-meta mt-2 max-w-2xl leading-relaxed">{description}</p> : null}
      </div>
      {actions}
    </div>
  );
}
