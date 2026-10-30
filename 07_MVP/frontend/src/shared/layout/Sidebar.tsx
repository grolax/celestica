import { NavLink, useNavigate } from "react-router-dom";
import Icon from "@/shared/components/Icon";

export default function Sidebar({ collapsed }: { collapsed: boolean }) {
  const navigate = useNavigate();
  const cls = ({ isActive }: { isActive: boolean }) => `sidebar-link ${isActive ? "active" : ""}`;

  return (
    <nav className={`sidebar ${collapsed ? "collapsed" : ""}`}>
      <button className="btn btn-primary" style={{ margin: "0 0 12px" }} onClick={() => navigate("/proyectos/nuevo")}>
        + Nuevo proyecto
      </button>
      <NavLink to="/proyectos" end className={cls}><Icon name="folder" /> Mis proyectos</NavLink>
      <div className="sidebar-section">Recursos</div>
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
