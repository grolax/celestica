import { ReactNode } from "react";

export default function Table({ headers, children }: { headers: ReactNode[]; children: ReactNode }) {
  return (
    <div className="table-wrap">
      <table className="si">
        <thead>
          <tr>{headers.map((h, i) => <th key={i}>{h}</th>)}</tr>
        </thead>
        <tbody>{children}</tbody>
      </table>
    </div>
  );
}

export function ConfBadge({ value }: { value: number | null | undefined }) {
  if (typeof value !== "number") return null;
  const cls = value >= 0.85 ? "conf-high" : value >= 0.6 ? "conf-mid" : "conf-low";
  return <span className={`conf-badge ${cls}`}>{value.toFixed(2)}</span>;
}
