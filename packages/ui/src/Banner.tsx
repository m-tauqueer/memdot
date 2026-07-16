import type { ReactNode } from "react";

export type BannerTone = "info" | "warning" | "danger" | "success";

export type BannerProps = {
  title: string;
  description?: string;
  tone?: BannerTone;
  action?: ReactNode;
  live?: "polite" | "assertive" | "off";
};

export function Banner({
  title,
  description,
  tone = "info",
  action,
  live = "polite",
}: BannerProps) {
  return (
    <div
      className={`md-banner md-banner-${tone}`}
      role={live === "off" ? undefined : "status"}
      aria-live={live === "off" ? undefined : live}
    >
      <div className="md-banner-copy">
        <p className="md-banner-title">{title}</p>
        {description ? <p className="md-banner-desc">{description}</p> : null}
      </div>
      {action ? <div className="md-banner-action">{action}</div> : null}
    </div>
  );
}
