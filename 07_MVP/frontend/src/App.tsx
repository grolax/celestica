import { useState } from "react";
import { BrowserRouter, Navigate, Outlet, Route, Routes, useLocation } from "react-router-dom";
import { AuthProvider, useAuth } from "@/features/auth/useAuth";
import Header from "@/shared/layout/Header";
import Sidebar from "@/shared/layout/Sidebar";
import LoginPage, { SignupPage } from "@/features/auth/LoginPage";
import ChangePasswordPage from "@/features/auth/ChangePasswordPage";
import LandingPage from "@/features/landing/LandingPage";
import ProjectList from "@/features/projects/ProjectList";
import NewProject from "@/features/projects/NewProject";
import ProjectView from "@/features/projects/ProjectView";
import ProjectDashboard from "@/features/projects/ProjectDashboard";
import LexicalAnalysis from "@/features/analysis/lexical/LexicalAnalysis";
import Codebook from "@/features/analysis/codebook/Codebook";
import Coding from "@/features/analysis/coding/Coding";
import Traceability from "@/features/analysis/traceability/Traceability";
import ReportView from "@/features/analysis/report/ReportView";
import AuditLog from "@/features/analysis/audit/AuditLog";
import ExportReport from "@/features/export/ExportReport";
import Settings from "@/features/settings/Settings";
import Documentation from "@/features/docs/Documentation";

function ProtectedLayout() {
  const { user, isAuthenticated, loading } = useAuth();
  const { pathname } = useLocation();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  if (loading) {
    return (
      <div style={{ display: "grid", placeItems: "center", minHeight: "100vh" }}>
        <span className="spinner dark" style={{ width: 28, height: 28 }} />
      </div>
    );
  }
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  if (user?.debe_cambiar_password && pathname !== "/cambiar-contrasena") {
    return <Navigate to="/cambiar-contrasena" replace />;
  }
  if (pathname === "/cambiar-contrasena") return <Outlet />; // pantalla centrada, sin menú

  return (
    <div className="app-shell">
      <Header onToggleSidebar={() => setSidebarCollapsed((c) => !c)} />
      <Sidebar collapsed={sidebarCollapsed} />
      <main className={`main-content ${sidebarCollapsed ? "full" : ""}`}>
        <Outlet />
      </main>
    </div>
  );
}

function PublicOnly({ children }: { children: JSX.Element }) {
  const { isAuthenticated, loading } = useAuth();
  if (loading) return null;
  if (isAuthenticated) return <Navigate to="/proyectos" replace />;
  return children;
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<PublicOnly><LoginPage /></PublicOnly>} />
          <Route path="/signup" element={<PublicOnly><SignupPage /></PublicOnly>} />
          <Route element={<ProtectedLayout />}>
            <Route path="/proyectos" element={<ProjectList />} />
            <Route path="/proyectos/nuevo" element={<NewProject />} />
            <Route path="/proyectos/:id" element={<ProjectView />}>
              <Route index element={<ProjectDashboard />} />
              <Route path="lexico" element={<LexicalAnalysis />} />
              <Route path="codigos" element={<Codebook />} />
              <Route path="codificacion" element={<Coding />} />
              <Route path="trazabilidad" element={<Traceability />} />
              <Route path="informe" element={<ReportView />} />
              <Route path="exportar" element={<ExportReport />} />
              <Route path="auditoria" element={<AuditLog />} />
            </Route>
            <Route path="/cambiar-contrasena" element={<ChangePasswordPage />} />
            <Route path="/configuracion" element={<Settings />} />
            <Route path="/documentacion" element={<Documentation />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
