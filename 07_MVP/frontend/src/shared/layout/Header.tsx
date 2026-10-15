import { Link } from "react-router-dom";
import { useAuth } from "@/features/auth/useAuth";
import Button from "@/shared/components/Button";
import Icon from "@/shared/components/Icon";

export default function Header({ onToggleSidebar }: { onToggleSidebar: () => void }) {
  const { user, logout } = useAuth();
  const initials = (user?.nombre || user?.email || "?")
    .split(/[\s@]/)
    .filter(Boolean)
    .slice(0, 2)
    .map((s) => s[0]!.toUpperCase())
    .join("");

  return (
    <header className="app-header">
      <button
        className="btn btn-ghost btn-sm"
        onClick={onToggleSidebar}
        aria-label="Mostrar u ocultar menú"
        title="Mostrar u ocultar menú"
      >
        <Icon name="menu" size={20} />
      </button>
      <Link to="/" className="logo">
        <span className="logo-mark">C</span>
        <span>Celestica</span>
      </Link>
      <div className="header-user">
        <div className="avatar" title={user?.email}>{initials}</div>
        <div className="small" style={{ lineHeight: 1.3 }}>
          <strong>{user?.nombre || user?.email}</strong>
          {user?.empresa && <div className="muted">{user.empresa}</div>}
        </div>
        <Button variant="ghost" size="sm" onClick={logout}>Salir</Button>
      </div>
    </header>
  );
}
