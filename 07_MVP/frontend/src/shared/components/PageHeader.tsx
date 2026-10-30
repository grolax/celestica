import { ReactNode } from "react";

// level 1: título de pantalla (h1). level 2: título de pestaña de proyecto (h2).
export default function PageHeader({ title, help, level = 1, children }: { title: string; help: string; level?: 1 | 2; children?: ReactNode }) {
  const Heading = level === 1 ? "h1" : "h2";
  return (
    <header className="page-header">
      <div>
        <Heading>{title}</Heading>
        <p className="muted">{help}</p>
      </div>
      {children}
    </header>
  );
}
