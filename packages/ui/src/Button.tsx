import type { ButtonHTMLAttributes } from "react";

export type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  label: string;
};

export function Button({ label, type = "button", ...rest }: ButtonProps) {
  return (
    <button type={type} {...rest}>
      {label}
    </button>
  );
}
