import type { InputHTMLAttributes } from "react";

export type InputProps = InputHTMLAttributes<HTMLInputElement> & {
  label?: string;
  hint?: string;
};

export function Input({ label, hint, id, className = "", ...rest }: InputProps) {
  const inputId = id ?? (label ? label.toLowerCase().replace(/\s+/g, "-") : undefined);
  return (
    <label className="md-field" htmlFor={inputId}>
      {label ? <span className="md-label">{label}</span> : null}
      <input id={inputId} className={`md-input ${className}`.trim()} {...rest} />
      {hint ? <span className="md-hint">{hint}</span> : null}
    </label>
  );
}
