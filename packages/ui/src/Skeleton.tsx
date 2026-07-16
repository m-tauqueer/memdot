export type SkeletonProps = {
  className?: string;
  height?: number | string;
  width?: number | string;
  "aria-label"?: string;
};

export function Skeleton({
  className = "",
  height = 16,
  width = "100%",
  "aria-label": ariaLabel = "Loading",
}: SkeletonProps) {
  return (
    <div
      className={`md-skeleton ${className}`.trim()}
      style={{ height, width }}
      role="status"
      aria-label={ariaLabel}
    />
  );
}
