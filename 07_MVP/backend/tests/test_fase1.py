"""Verificación Fase 1 (Mongo) con mongomock — sin tocar la API de Claude."""
import io
import sys

import mongomock

# Inyectar mongomock ANTES de importar la app
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import database
database._client = mongomock.MongoClient()

from fastapi.testclient import TestClient
from app.main import app

c = TestClient(app, raise_server_exceptions=False)
FAILS = []

def check(name, cond, extra=""):
    print(("PASS  " if cond else "FAIL  ") + name + (f"  [{extra}]" if extra and not cond else ""))
    if not cond:
        FAILS.append(name)

# ---- signup / login / me ----
r = c.post("/auth/signup", json={"email": "ana@udp.cl", "password": "clave12345", "nombre": "Ana", "empresa": "UDP"})
check("signup", r.status_code == 200, r.text)
tok_a = r.json()["token"]
ha = {"Authorization": f"Bearer {tok_a}"}

r = c.post("/auth/signup", json={"email": "ana@udp.cl", "password": "clave12345"})
check("signup duplicado -> 409", r.status_code == 409, r.text)

r = c.post("/auth/login", json={"email": "ana@udp.cl", "password": "clave12345"})
check("login", r.status_code == 200, r.text)

r = c.get("/auth/me", headers=ha)
check("me", r.status_code == 200 and r.json()["email"] == "ana@udp.cl", r.text)

r = c.get("/api/projects")
check("sin token -> 401", r.status_code == 401, r.text)

# ---- crear proyecto ----
csv = "id_alumno,respuesta\n" + "\n".join(f"A{i},El profesor explica con claridad y buenos ejemplos pero las pruebas son muy dificiles ({i})" for i in range(1, 31))
r = c.post("/api/projects", headers=ha,
           files={"file": ("demo.csv", io.BytesIO(csv.encode()), "text/csv")},
           data={"name": "Demo Mongo", "marco_teorico": "Marco de prueba", "template": "evaluacion_docente_cna"})
check("crear proyecto", r.status_code == 200, r.text)
pid = r.json()["id"]
check("30 respuestas", r.json()["n_responses"] == 30, r.text)

r = c.get(f"/api/projects/{pid}", headers=ha)
check("get proyecto", r.status_code == 200, r.text)
cats = r.json()["categories"]
check("plantilla aplicada (4 categorias)", len(cats) == 4, str(len(cats)))

r = c.get("/api/projects", headers=ha)
check("list_projects (aggregation)", r.status_code == 200 and len(r.json()) == 1 and r.json()[0]["n_responses"] == 30 and r.json()[0]["n_categories"] == 4, r.text)

# ---- léxico (sin IA: interpret falla en silencio) ----
r = c.post(f"/api/projects/{pid}/lexical", headers=ha)
check("analisis lexico", r.status_code == 200, r.text[:200])
r = c.get("/api/projects", headers=ha)
check("has_lexical en lista", r.json()[0]["has_lexical"] is True, r.text)

# ---- categorías: update parcial ($set posicional) ----
cid = cats[0]["id"]
r = c.patch(f"/api/projects/{pid}/categories/{cid}", headers=ha, json={"status": "validada", "definicion": "Definicion editada"})
check("validar categoria ($set)", r.status_code == 200 and r.json()["status"] == "validada", r.text)
r = c.get(f"/api/projects/{pid}", headers=ha)
cat0 = [x for x in r.json()["categories"] if x["id"] == cid][0]
check("cambio persistido y campos intactos", cat0["definicion"] == "Definicion editada" and cat0["nombre"] == cats[0]["nombre"] and cat0["criterios_inclusion"] == cats[0]["criterios_inclusion"], str(cat0))

# ---- categoría manual ($push) ----
r = c.post(f"/api/projects/{pid}/categories", headers=ha, json={"nombre": "Manual X", "definicion": "d"})
check("categoria manual", r.status_code == 200 and r.json()["status"] == "validada", r.text)
mcid = r.json()["id"]

# ---- comentarios ($push / $pull) ----
r = c.post(f"/api/projects/{pid}/categories/{cid}/comments", headers=ha, json={"text": "revisar criterios"})
check("comentario $push", r.status_code == 200, r.text)
com_id = r.json()["id"]
r = c.get(f"/api/projects/{pid}", headers=ha)
cat0 = [x for x in r.json()["categories"] if x["id"] == cid][0]
check("comentario persistido", len(cat0.get("comments", [])) == 1, str(cat0.get("comments")))
r = c.delete(f"/api/projects/{pid}/categories/{cid}/comments/{com_id}", headers=ha)
check("comentario $pull", r.status_code == 200, r.text)
r = c.delete(f"/api/projects/{pid}/categories/{cid}/comments/nope", headers=ha)
check("comentario inexistente -> 404", r.status_code == 404, r.text)

# ---- recodificación manual ($set codings.RID) ----
r = c.put(f"/api/projects/{pid}/responses/R0001/codings", headers=ha, json={"category_ids": [cid, mcid]})
check("recodificacion manual", r.status_code == 200 and len(r.json()) == 2, r.text)
r = c.get(f"/api/projects/{pid}/responses", headers=ha)
a1 = [x for x in r.json()["items"] if x["id"] == "R0001"][0]
check("coding persistido en R0001", len(a1["codings"]) == 2 and a1["codings"][0]["source"] == "analista", str(a1["codings"]))

# ---- summary + export PDF/CSV (sin IA) ----
r = c.get(f"/api/projects/{pid}/summary", headers=ha)
check("summary", r.status_code == 200 and r.json()["n_coded"] == 1, r.text[:200])
r = c.get(f"/api/projects/{pid}/export/pdf", headers=ha)
check("export PDF", r.status_code == 200 and r.content[:4] == b"%PDF", str(r.status_code))
r = c.get(f"/api/projects/{pid}/export/csv", headers=ha)
check("export CSV", r.status_code == 200, r.text[:100])
r = c.get(f"/api/projects/{pid}/export/xlsx", headers=ha)
check("export XLSX", r.status_code == 200, str(r.status_code))
r = c.get(f"/api/projects/{pid}/export/docx", headers=ha)
check("export DOCX", r.status_code == 200, str(r.status_code))

# ---- auditoría: eventos en el doc y en la colección ----
r = c.get(f"/api/projects/{pid}/audit", headers=ha)
actions = [e["action"] for e in r.json()]
expected = ["creacion_proyecto", "aplicacion_plantilla", "analisis_lexico", "validacion_categoria",
            "creacion_categoria_manual", "comentario_categoria", "eliminacion_comentario", "recodificacion_manual"]
missing = [a for a in expected if a not in actions]
check("audit log completo en doc", not missing, f"faltan {missing}; hay {actions}")
dups = len(actions) != len(set(e["id"] for e in r.json()))
check("audit sin duplicados", not dups, str(actions))
n_col = database.get_db().audit_events.count_documents({"project_id": pid})
check("audit_events (coleccion) pobladas", n_col == len(actions), f"col={n_col} doc={len(actions)}")

# ---- MULTI-TENANT: acceso cruzado ----
r = c.post("/auth/signup", json={"email": "intruso@x.cl", "password": "clave12345"})
hb = {"Authorization": f"Bearer {r.json()['token']}"}
for method, url in [("get", f"/api/projects/{pid}"), ("get", f"/api/projects/{pid}/audit"),
                    ("get", f"/api/projects/{pid}/export/pdf"), ("delete", f"/api/projects/{pid}"),
                    ("post", f"/api/projects/{pid}/lexical")]:
    r = getattr(c, method)(url, headers=hb)
    check(f"cruzado {method.upper()} {url.split('/')[-1]} -> 404", r.status_code == 404, str(r.status_code))
r = c.patch(f"/api/projects/{pid}/categories/{cid}", headers=hb, json={"status": "descartada"})
check("cruzado PATCH categoria -> 404", r.status_code == 404, str(r.status_code))
r = c.get("/api/projects", headers=hb)
check("intruso ve 0 proyectos", r.json() == [], r.text)
# verificar que nada cambió
r = c.get(f"/api/projects/{pid}", headers=ha)
check("proyecto intacto tras intento cruzado", r.status_code == 200 and [x for x in r.json()["categories"] if x["id"] == cid][0]["status"] == "validada")

# ---- delete propio ----
r = c.delete(f"/api/projects/{pid}", headers=ha)
check("delete propio", r.status_code == 200, r.text)
check("audit_events limpiadas", database.get_db().audit_events.count_documents({"project_id": pid}) == 0)

print()
print("RESULTADO:", "TODO OK" if not FAILS else f"{len(FAILS)} FALLAS: {FAILS}")
sys.exit(1 if FAILS else 0)
