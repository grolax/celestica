import { NavLink } from "react-router-dom";
import Icon from "@/shared/components/Icon";

export default function Sidebar({ collapsed }: { collapsed: boolean }) {
  const cls = ({ isActive }: { isActive: boolean }) => `sidebar-link ${isActive ? "active" : ""}`;

  return (
    <nav className={`sidebar ${collapsed ? "collapsed" : ""}`}>
      <div className="sidebar-section">Trabajo</div>
      <NavLink to="/proyectos/nuevo" className={cls}><Icon name="plus" /> Nuevo proyecto</NavLink>
      <NavLink to="/proyectos" end className={cls}><Icon name="folder" /> Mis proyectos</NavLink>
      <div className="sidebar-section">Ayuda y configuración</div>
      <NavLink to="/documentacion" className={cls}><Icon name="book" /> Documentación</NavLink>
      <NavLink to="/configuracion" className={cls}><Icon name="settings" /> Configuración</NavLink>
      <div style={{ marginTop: "auto", padding: "12px 12px 4px" }} className="small muted">
        Celestica v1.1
        <br />
        Análisis auditable y trazable
      </div>
    </nav>
  );
}
