import type { ButtonHTMLAttributes, ReactNode } from "react";

export type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";
export type ButtonSize = "sm" | "md";

export type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  label?: string;
  children?: ReactNode;
  variant?: ButtonVariant;
  size?: ButtonSize;
};

const variantClass: Record<ButtonVariant, string> = {
  primary: "md-btn md-btn-primary",
  secondary: "md-btn md-btn-secondary",
  ghost: "md-btn md-btn-ghost",
  danger: "md-btn md-btn-danger",
};

const sizeClass: Record<ButtonSize, string> = {
  sm: "md-btn-sm",
  md: "md-btn-md",
};

export function Button({
  label,
  children,
  type = "button",
  variant = "primary",
  size = "md",
  className = "",
  ...rest
}: ButtonProps) {
  return (
    <button
      type={type}
      className={`${variantClass[variant]} ${sizeClass[size]} ${className}`.trim()}
      {...rest}
    >
      {children ?? label}
    </button>
  );
}
