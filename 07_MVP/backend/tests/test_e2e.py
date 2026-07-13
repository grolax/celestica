"""E2E v1.1: signup → proyecto (plantilla) → léxico → validar → codificar (IA
simulada) → trazabilidad → informe (streaming simulado) → exportar → auditoría
→ aislamiento multi-tenant. Sin gastar API de Claude."""
import io
import sys
import time

import mongomock

from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import database
database._client = mongomock.MongoClient()

from fastapi.testclient import TestClient
from app.main import app
from app.services import thematic

FAILS = []
def check(name, cond, extra=""):
    print(("PASS  " if cond else "FAIL  ") + name + (f"  [{extra}]" if extra and not cond else ""))
    if not cond:
        FAILS.append(name)

# ---- IA simulada ----
def fake_codify_all(marco, categories, responses, batch_size=25, progress_cb=None):
    out = []
    for i, r in enumerate(responses):
        cat = categories[i % len(categories)]
        out.append({"response_id": r["id"], "assignments": [
            {"category_id": cat["id"], "rationale": "Coincide con criterios de inclusión.", "confidence": 0.87 if i % 3 else 0.55}]})
        if progress_cb and (i + 1) % batch_size == 0:
            progress_cb(i + 1, len(responses))
    if progress_cb:
        progress_cb(len(responses), len(responses))
    return out

FAKE_REPORT = "RESUMEN INTERPRETATIVO\n\nHallazgo central del corpus.\n\nTENSIONES OBSERVADAS\n\nExigencia versus claridad."
def fake_report(marco_teorico, categories, codings, responses, lexical_data, progress_cb=None):
    if progress_cb:
        for i in range(3):
            progress_cb(FAKE_REPORT[: (i + 1) * len(FAKE_REPORT) // 3])
            time.sleep(0.1)
    return FAKE_REPORT

thematic.codify_all = fake_codify_all
thematic.generate_qualitative_report = fake_report

c = TestClient(app, raise_server_exceptions=False)

# 1. signup
r = c.post("/auth/signup", json={"email": "demo@udp.cl", "password": "clave12345", "nombre": "Demo", "empresa": "UDP"})
check("1. signup", r.status_code == 200, r.text)
h = {"Authorization": f"Bearer {r.json()['token']}"}

# 2. proyecto con plantilla (CSV estilo dataset demo)
rows = ["id_respuesta,respuesta"]
frases = ["El profesor domina la materia y responde todo",
          "Las clases son claras y con buenos ejemplos practicos",
          "Las pruebas no se condicen con lo pasado en catedra",
          "Muy buena disposicion para resolver dudas fuera de horario"]
for i in range(1, 41):
    rows.append(f"E{i:03d},{frases[i % 4]} ({i})")
csv = "\n".join(rows)
r = c.post("/api/projects", headers=h,
           files={"file": ("demo.csv", io.BytesIO(csv.encode()), "text/csv")},
           data={"name": "Evaluación Docente 2026-1", "template": "evaluacion_docente_cna"})
check("2. crear proyecto con plantilla", r.status_code == 200 and r.json()["n_responses"] == 40, r.text)
pid = r.json()["id"]

# 3. plantillas agrupadas
r = c.get("/api/framework-templates", headers=h)
inds = {t["industria"] for t in r.json()}
check("3. 12 plantillas / 5 industrias", len(r.json()) == 12 and len(inds) == 5, str(inds))

# 4. léxico
r = c.post(f"/api/projects/{pid}/lexical", headers=h)
check("4. analisis lexico", r.status_code == 200 and r.json()["n_responses"] == 40, r.text[:150])

# 5. validar las 4 categorías de plantilla
cats = c.get(f"/api/projects/{pid}", headers=h).json()["categories"]
for cat in cats:
    r = c.patch(f"/api/projects/{pid}/categories/{cat['id']}", headers=h, json={"status": "validada"})
check("5. validar 4 categorias", all(x["status"] == "validada" for x in c.get(f"/api/projects/{pid}", headers=h).json()["categories"]))

# 6. codificar con progreso
r = c.post(f"/api/projects/{pid}/codify", headers=h)
check("6. codify started", r.json().get("status") == "started", r.text)
for _ in range(40):
    time.sleep(0.2)
    p = c.get(f"/api/projects/{pid}/codify/progress", headers=h).json()
    if p["status"] in ("done", "error"):
        break
check("6b. codify done 40/40", p.get("status") == "done" and p.get("coded") == 40, str(p))

# 7. trazabilidad
rows = c.get(f"/api/projects/{pid}/export/traceability", headers=h).json()
check("7. trazabilidad 40 filas", len(rows) == 40, str(len(rows)))
r = c.get(f"/api/projects/{pid}/summary", headers=h)
check("7b. summary coherente", r.json()["n_coded"] == 40 and r.json()["n_categories_validated"] == 4, r.text[:200])

# 8. informe con progreso
r = c.post(f"/api/projects/{pid}/report", headers=h)
check("8. report started", r.json().get("status") == "started", r.text)
for _ in range(40):
    time.sleep(0.2)
    p = c.get(f"/api/projects/{pid}/report/progress", headers=h).json()
    if p["status"] in ("done", "error"):
        break
check("8b. report done", p["status"] == "done", str(p))
r = c.get(f"/api/projects/{pid}/report", headers=h)
check("8c. informe guardado", "RESUMEN INTERPRETATIVO" in r.json()["report"], r.text[:100])

# 9. exportaciones
r = c.get(f"/api/projects/{pid}/export/pdf", headers=h)
check("9. PDF valido", r.status_code == 200 and r.content[:4] == b"%PDF" and len(r.content) > 5000, str(len(r.content)))
for fmt in ("docx", "csv", "xlsx"):
    r = c.get(f"/api/projects/{pid}/export/{fmt}", headers=h)
    check(f"9b. export {fmt}", r.status_code == 200 and len(r.content) > 200, str(r.status_code))

# 10. auditoría completa
acts = [e["action"] for e in c.get(f"/api/projects/{pid}/audit", headers=h).json()]
need = ["creacion_proyecto", "aplicacion_plantilla", "analisis_lexico", "validacion_categoria",
        "codificacion_corpus", "generacion_informe_cualitativo"]
missing = [a for a in need if a not in acts]
check("10. auditoria completa", not missing, f"faltan {missing}")

# 11. multi-tenant
r2 = c.post("/auth/signup", json={"email": "otro@x.cl", "password": "clave12345"})
hb = {"Authorization": f"Bearer {r2.json()['token']}"}
codes = [c.get(f"/api/projects/{pid}", headers=hb).status_code,
         c.get(f"/api/projects/{pid}/export/pdf", headers=hb).status_code,
         c.get(f"/api/projects/{pid}/report/progress", headers=hb).status_code,
         c.delete(f"/api/projects/{pid}", headers=hb).status_code]
check("11. aislamiento multi-tenant (todo 404)", codes == [404, 404, 404, 404], str(codes))
check("11b. proyecto sigue vivo", c.get(f"/api/projects/{pid}", headers=h).status_code == 200)

print()
print("RESULTADO:", "TODO OK" if not FAILS else f"{len(FAILS)} FALLAS: {FAILS}")
sys.exit(1 if FAILS else 0)
