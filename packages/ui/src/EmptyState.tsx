import type { ReactNode } from "react";

export type EmptyStateProps = {
  title: string;
  description?: string;
  action?: ReactNode;
};

export function EmptyState({ title, description, action }: EmptyStateProps) {
  return (
    <div className="md-empty" role="status">
      <h2 className="md-empty-title">{title}</h2>
      {description ? <p className="md-empty-desc">{description}</p> : null}
      {action ? <div className="md-empty-action">{action}</div> : null}
    </div>
  );
}
