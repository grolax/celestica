import { ButtonHTMLAttributes, ReactNode } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "danger" | "success" | "ghost";
  size?: "sm" | "md" | "lg";
  block?: boolean;
  busy?: boolean;
  children: ReactNode;
}

export default function Button({
  variant = "primary", size = "md", block = false, busy = false,
  children, className = "", disabled, ...rest
}: ButtonProps) {
  const classes = [
    "btn",
    `btn-${variant}`,
    size === "sm" ? "btn-sm" : size === "lg" ? "btn-lg" : "",
    block ? "btn-block" : "",
    className,
  ].filter(Boolean).join(" ");
  return (
    <button className={classes} disabled={disabled || busy} {...rest}>
      {busy && <span className={`spinner ${variant !== "primary" ? "dark" : ""}`} />}
      {children}
    </button>
  );
}
