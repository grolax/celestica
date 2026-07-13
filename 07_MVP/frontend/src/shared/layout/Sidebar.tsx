import { NavLink, useNavigate } from "react-router-dom";

export default function Sidebar({ collapsed }: { collapsed: boolean }) {
  const navigate = useNavigate();
  const cls = ({ isActive }: { isActive: boolean }) => `sidebar-link ${isActive ? "active" : ""}`;

  return (
    <nav className={`sidebar ${collapsed ? "collapsed" : ""}`}>
      <button className="btn btn-primary" style={{ margin: "0 0 12px" }} onClick={() => navigate("/proyectos/nuevo")}>
        + Nuevo proyecto
      </button>
      <NavLink to="/" end className={cls}>📁 Mis proyectos</NavLink>
      <div className="sidebar-section">Recursos</div>
      <NavLink to="/documentacion" className={cls}>📖 Documentación</NavLink>
      <NavLink to="/configuracion" className={cls}>⚙️ Configuración</NavLink>
      <div style={{ marginTop: "auto", padding: "12px 12px 4px" }} className="small muted">
        SoftInsight v1.1
        <br />
        Análisis auditable y trazable
      </div>
    </nav>
  );
}
