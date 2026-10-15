import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "./useAuth";
import Button from "@/shared/components/Button";
import Input from "@/shared/components/Input";

function AuthHero() {
  return (
    <div className="auth-hero">
      <h1>Análisis cualitativo asistido por IA, auditable de principio a fin.</h1>
      <p>
        Celestica transforma semanas de codificación manual de encuestas abiertas en un
        proceso de días — sin sacrificar rigor metodológico.
      </p>
      <ul>
        <li>Análisis léxico y temático anclado a tu marco teórico</li>
        <li>Cada decisión de la IA es validada por tu equipo</li>
        <li>Trazabilidad completa para auditoría y acreditación (CNA/CNE, ISO)</li>
        <li>Reportes PDF y Word listos para archivar</li>
      </ul>
    </div>
  );
}

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await login(email.trim(), password);
      navigate("/");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-page">
      <AuthHero />
      <div className="auth-form-side">
        <form className="auth-card" onSubmit={submit}>
          <div className="logo" style={{ marginBottom: 18 }}>
            <span className="logo-mark">C</span>
            <span>Celestica</span>
          </div>
          <h2>Iniciar sesión</h2>
          {error && <div className="alert alert-error">{error}</div>}
          <Input label="Email" type="email" value={email} required autoFocus
                 onChange={(e) => setEmail(e.target.value)} placeholder="tu@organizacion.cl" />
          <Input label="Contraseña" type="password" value={password} required
                 onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" />
          <div style={{ marginTop: 18 }}>
            <Button type="submit" block busy={busy}>Ingresar</Button>
          </div>
          <p className="small muted" style={{ marginTop: 16, textAlign: "center" }}>
            ¿No tienes cuenta? <Link to="/signup">Regístrate</Link>
          </p>
        </form>
      </div>
    </div>
  );
}

export function SignupPage() {
  const { signup } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ nombre: "", empresa: "", email: "", password: "", confirm: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const set = (k: keyof typeof form) => (e: { target: { value: string } }) =>
    setForm((f) => ({ ...f, [k]: e.target.value }));

  const passwordError =
    form.password && form.password.length < 8 ? "Mínimo 8 caracteres" : "";
  const confirmError =
    form.confirm && form.confirm !== form.password ? "Las contraseñas no coinciden" : "";

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (passwordError || confirmError) return;
    setBusy(true);
    setError("");
    try {
      await signup(form.email.trim(), form.password, form.nombre.trim(), form.empresa.trim());
      navigate("/");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-page">
      <AuthHero />
      <div className="auth-form-side">
        <form className="auth-card" onSubmit={submit}>
          <div className="logo" style={{ marginBottom: 18 }}>
            <span className="logo-mark">C</span>
            <span>Celestica</span>
          </div>
          <h2>Crear cuenta</h2>
          {error && <div className="alert alert-error">{error}</div>}
          <Input label="Nombre" value={form.nombre} required autoFocus
                 onChange={set("nombre")} placeholder="Ej: Francisco Salazar" />
          <Input label="Institución / Empresa" value={form.empresa}
                 onChange={set("empresa")} placeholder="Ej: Universidad Diego Portales, CADEM, SernacFacilita" />
          <Input label="Email" type="email" value={form.email} required
                 onChange={set("email")} placeholder="tu@organizacion.cl" />
          <Input label="Contraseña" type="password" value={form.password} required
                 onChange={set("password")} error={passwordError} placeholder="Mínimo 8 caracteres" />
          <Input label="Confirmar contraseña" type="password" value={form.confirm} required
                 onChange={set("confirm")} error={confirmError} placeholder="Repite la contraseña" />
          <div style={{ marginTop: 18 }}>
            <Button type="submit" block busy={busy}>Crear cuenta</Button>
          </div>
          <p className="small muted" style={{ marginTop: 16, textAlign: "center" }}>
            ¿Ya tienes cuenta? <Link to="/login">Inicia sesión</Link>
          </p>
        </form>
      </div>
    </div>
  );
}
