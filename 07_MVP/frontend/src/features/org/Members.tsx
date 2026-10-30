import { FormEvent, useEffect, useState } from "react";
import { useAuth } from "@/features/auth/useAuth";
import { Rol, ROL_LABEL } from "@/features/auth/api";
import Button from "@/shared/components/Button";
import Card from "@/shared/components/Card";
import Input from "@/shared/components/Input";
import PageHeader from "@/shared/components/PageHeader";
import Table from "@/shared/components/Table";
import { useAsync } from "@/shared/hooks/useAsync";
import { Member, orgApi } from "./api";

const ROLES: Rol[] = ["lector", "analista", "admin"];
const ROL_AYUDA: Record<Rol, string> = {
  lector: "Ve resultados, descarga informes y comenta.",
  analista: "Hace todo el análisis, incluido crear y borrar proyectos.",
  admin: "Lo mismo que el analista, más la gestión de miembros.",
};

export default function Members() {
  const { user } = useAuth();
  const { busy, error, run } = useAsync();
  const [members, setMembers] = useState<Member[] | null>(null);
  const [form, setForm] = useState<{ email: string; nombre: string; rol: Rol }>({ email: "", nombre: "", rol: "lector" });
  // Solo en memoria: se pierde al salir de la pantalla y nunca se persiste.
  const [temp, setTemp] = useState<{ nombre: string; password: string } | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => { run(() => orgApi.list().then(setMembers)); }, [run]);

  const replace = (m: Member) => setMembers((ms) => ms && ms.map((x) => (x.id === m.id ? m : x)));

  async function add(e: FormEvent) {
    e.preventDefault();
    const r = await run(() => orgApi.create({ ...form, email: form.email.trim(), nombre: form.nombre.trim() }));
    if (!r) return;
    setMembers((ms) => [...(ms ?? []), r.member]);
    setTemp({ nombre: r.member.nombre, password: r.password_temporal });
    setCopied(false);
    setForm({ email: "", nombre: "", rol: "lector" });
  }

  async function changeRole(m: Member, rol: Rol) {
    if (rol === m.rol || !confirm(`¿Cambiar el rol de ${m.nombre} a ${ROL_LABEL[rol]}?`)) return;
    const r = await run(() => orgApi.update(m.id, { rol }));
    if (r) replace(r);
  }

  async function toggleActive(m: Member) {
    if (m.activo && !confirm(`¿Desactivar a ${m.nombre}? No podrá entrar hasta que la reactives.`)) return;
    const r = await run(() => orgApi.update(m.id, { activo: !m.activo }));
    if (r) replace(r);
  }

  async function copy() {
    try {
      await navigator.clipboard.writeText(temp!.password);
      setCopied(true);
    } catch {
      setCopied(false); // sin permiso del navegador: la contraseña sigue visible para copiarla a mano
    }
  }

  return (
    <>
      <PageHeader title="Miembros" help="Las personas de tu organización y lo que puede hacer cada una." />
      {error && <div className="alert alert-error" role="alert">{error}</div>}
      {temp && (
        <div className="alert alert-success" role="status">
          <p style={{ margin: "0 0 8px" }}>
            Entrega esta contraseña temporal a {temp.nombre}. Por seguridad no se volverá a mostrar; al entrar, deberá cambiarla.
          </p>
          <code style={{ fontSize: 16, marginRight: 10 }}>{temp.password}</code>
          <Button size="sm" variant="secondary" onClick={copy}>{copied ? "Copiada" : "Copiar"}</Button>
        </div>
      )}

      <Card title="Qué puede hacer cada rol">
        <ul style={{ margin: 0, paddingLeft: 20 }}>
          {ROLES.map((r) => <li key={r}><strong>{ROL_LABEL[r]}:</strong> {ROL_AYUDA[r]}</li>)}
        </ul>
      </Card>

      <Card title="Agregar miembro">
        <form onSubmit={add} style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 12, alignItems: "end" }}>
          <Input label="Email" type="email" required value={form.email} autoComplete="off"
                 onChange={(e) => setForm({ ...form, email: e.target.value })} />
          <Input label="Nombre" type="text" required value={form.nombre} autoComplete="off"
                 onChange={(e) => setForm({ ...form, nombre: e.target.value })} />
          <div>
            <label className="field-label" htmlFor="rol_nuevo">Rol</label>
            <select id="rol_nuevo" value={form.rol} onChange={(e) => setForm({ ...form, rol: e.target.value as Rol })}>
              {ROLES.map((r) => <option key={r} value={r}>{ROL_LABEL[r]}</option>)}
            </select>
          </div>
          <div><Button type="submit" busy={busy}>Agregar miembro</Button></div>
        </form>
      </Card>

      <Card title="Equipo">
        {!members ? (
          error ? null : <p className="muted">Cargando miembros…</p>
        ) : (
          <Table headers={["Nombre", "Email", "Rol", "Estado", "Acción"]}>
            {members.map((m) => (
              <tr key={m.id} className={m.activo ? "" : "muted"}>
                <td>{m.nombre}{m.id === user?.id && " (tú)"}</td>
                <td>{m.email}</td>
                <td>
                  <select aria-label={`Rol de ${m.nombre}`} value={m.rol} disabled={busy}
                          onChange={(e) => changeRole(m, e.target.value as Rol)}>
                    {ROLES.map((r) => <option key={r} value={r}>{ROL_LABEL[r]}</option>)}
                  </select>
                </td>
                <td><span className={`pill ${m.activo ? "ok" : "neutro"}`}>{m.activo ? "Activo" : "Desactivado"}</span></td>
                <td>
                  <Button size="sm" variant={m.activo ? "danger" : "secondary"} disabled={busy} onClick={() => toggleActive(m)}>
                    {m.activo ? "Desactivar" : "Reactivar"}
                  </Button>
                </td>
              </tr>
            ))}
          </Table>
        )}
      </Card>
    </>
  );
}
