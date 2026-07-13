import { ReactNode } from "react";

export default function Card({
  title, actions, children, className = "",
}: {
  title?: ReactNode;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={`card ${className}`}>
      {(title || actions) && (
        <div className="card-title">
          {typeof title === "string" ? <h3>{title}</h3> : title}
          {actions && <div style={{ display: "flex", gap: 8, flexShrink: 0 }}>{actions}</div>}
        </div>
      )}
      {children}
    </div>
  );
}

export function StatCard({ value, label, accent = false }: { value: ReactNode; label: string; accent?: boolean }) {
  return (
    <div className={`stat-card ${accent ? "accent" : ""}`}>
      <div className="stat-value">{value}</div>
      <div className="stat-label">{label}</div>
    </div>
  );
}
