import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "./useAuth";
import { AuthLayout } from "./LoginPage";
import Button from "@/shared/components/Button";
import Input from "@/shared/components/Input";

export default function ChangePasswordPage() {
  const { user, changePassword, logout } = useAuth();
  const navigate = useNavigate();
  const obligatorio = !!user?.debe_cambiar_password;
  const [form, setForm] = useState({ actual: "", nueva: "", confirm: "" });
  const [backendError, setBackendError] = useState("");
  const [busy, setBusy] = useState(false);

  const set = (k: keyof typeof form) => (e: { target: { value: string } }) => {
    setBackendError(""); // el error del servidor corresponde al intento anterior
    setForm((f) => ({ ...f, [k]: e.target.value }));
  };

  const nuevaError = form.nueva && form.nueva.length < 8 ? "Mínimo 8 caracteres" : "";
  const confirmError = form.confirm && form.confirm !== form.nueva ? "Las contraseñas no coinciden" : "";
  // El backend no dice el campo: "no es correcta" es de la actual; el resto de sus mensajes, de la nueva.
  const actualError = /no es correcta/.test(backendError) ? backendError : "";
  const nuevaBackendError = backendError.startsWith("La contraseña") && !actualError ? backendError : "";
  const alertError = backendError && !actualError && !nuevaBackendError ? backendError : "";

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (nuevaError || form.nueva !== form.confirm) return; // la confirmación no llama al backend
    setBusy(true);
    setBackendError("");
    try {
      await changePassword(form.actual, form.nueva);
      if (obligatorio) navigate("/proyectos");
      else navigate("/configuracion", { state: { passwordChanged: true } });
    } catch (err) {
      setBackendError((err as Error).message);
      setBusy(false);
    }
  }

  return (
    <AuthLayout>
      <form className="auth-card" onSubmit={submit}>
        <h1>Cambiar contraseña</h1>
        {obligatorio && (
          <div className="alert alert-info">
            Por seguridad, cambia la contraseña temporal que te entregó tu administrador antes de continuar.
          </div>
        )}
        {alertError && <div className="alert alert-error" role="alert">{alertError}</div>}
        <Input label="Contraseña actual" type="password" value={form.actual} required autoFocus
               autoComplete="current-password" onChange={set("actual")} error={actualError} />
        <Input label="Contraseña nueva" type="password" value={form.nueva} required
               autoComplete="new-password" onChange={set("nueva")} error={nuevaError || nuevaBackendError}
               placeholder="Mínimo 8 caracteres" />
        <Input label="Confirmar contraseña nueva" type="password" value={form.confirm} required
               autoComplete="new-password" onChange={set("confirm")} error={confirmError}
               placeholder="Repite la contraseña nueva" />
        <div style={{ marginTop: 18, display: "flex", gap: 8 }}>
          <Button type="submit" busy={busy} block>Cambiar contraseña</Button>
          {obligatorio
            ? <Button type="button" variant="secondary" onClick={logout}>Salir</Button>
            : <Button type="button" variant="secondary" onClick={() => navigate("/configuracion")}>Cancelar</Button>}
        </div>
      </form>
    </AuthLayout>
  );
}
