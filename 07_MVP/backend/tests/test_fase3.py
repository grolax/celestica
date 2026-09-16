"""Fase 3: informe asíncrono con progreso — thematic simulado (sin API)."""
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

FAKE_REPORT = (
    "RESUMEN INTERPRETATIVO\n\nEl corpus muestra una tension central.\n\n"
    "HALLAZGOS PRINCIPALES\n\nLos estudiantes valoran la claridad.\n\n"
    "PREGUNTAS PARA PROFUNDIZAR\n\nQue explica la brecha observada."
)

def fake_report(marco_teorico, categories, codings, responses, lexical_data, progress_cb=None):
    # simular streaming: entregar el texto en 6 trozos con pausas
    acc = ""
    step = max(1, len(FAKE_REPORT) // 6)
    for i in range(0, len(FAKE_REPORT), step):
        acc = FAKE_REPORT[: i + step]
        if progress_cb:
            progress_cb(acc)
        time.sleep(0.35)
    return FAKE_REPORT

def fake_report_v2(survey_id, marco_teorico, categories, codings, responses,
                   columns, text_column, lexical_data=None, progress_cb=None, **kwargs):
    # simular flujo multi-prompt: progreso por respondente + síntesis + redacción
    total = len(responses) + 2
    for i in range(len(responses)):
        if progress_cb:
            progress_cb(f"Analizando respondentes ({i + 1}/{len(responses)})", i + 1, total)
        time.sleep(0.05)
    if progress_cb:
        progress_cb("Sintetizando clusters", len(responses), total)
        progress_cb("Redactando informe", len(responses) + 1, total)
        progress_cb("Informe completado", total, total)
    return FAKE_REPORT

thematic.generate_qualitative_report = fake_report
thematic.generate_qualitative_report_v2 = fake_report_v2

c = TestClient(app, raise_server_exceptions=False)
FAILS = []
def check(name, cond, extra=""):
    print(("PASS  " if cond else "FAIL  ") + name + (f"  [{extra}]" if extra and not cond else ""))
    if not cond:
        FAILS.append(name)

r = c.post("/auth/signup", json={"email": "f3@x.cl", "password": "clave12345"})
h = {"Authorization": f"Bearer {r.json()['token']}"}
csv = "respuesta\n" + "\n".join(f"El curso fue bueno pero exigente ({i})" for i in range(10))
r = c.post("/api/projects", headers=h,
           files={"file": ("d.csv", io.BytesIO(csv.encode()), "text/csv")},
           data={"name": "F3", "marco_teorico": "M"})
pid = r.json()["id"]

# sin categorías validadas -> 400
r = c.post(f"/api/projects/{pid}/report", headers=h)
check("informe sin categorias -> 400", r.status_code == 400, r.text)

# preparar: categoría manual validada + una codificación
r = c.post(f"/api/projects/{pid}/categories", headers=h, json={"nombre": "General", "definicion": "d"})
cid = r.json()["id"]
c.put(f"/api/projects/{pid}/responses/R0001/codings", headers=h, json={"category_ids": [cid]})

# progreso idle antes de partir
r = c.get(f"/api/projects/{pid}/report/progress", headers=h)
check("progress idle", r.json()["status"] == "idle", r.text)

# lanzar
r = c.post(f"/api/projects/{pid}/report", headers=h)
check("report -> started", r.status_code == 200 and r.json()["status"] == "started", r.text)

# observar progreso creciente con sección
seen_running = False
seen_section = None
for _ in range(30):
    time.sleep(0.3)
    p = c.get(f"/api/projects/{pid}/report/progress", headers=h).json()
    if p["status"] == "running":
        seen_running = True
        if p.get("section"):
            seen_section = p["section"]
    if p["status"] == "done":
        break
check("progreso running observado", seen_running)
check("seccion detectada en streaming", seen_section is not None, str(seen_section))
check("termina en done", p["status"] == "done", str(p))

# informe persistido con $set + evento auditado
r = c.get(f"/api/projects/{pid}/report", headers=h)
check("informe persistido", r.status_code == 200 and "RESUMEN INTERPRETATIVO" in r.json()["report"], r.text[:200])
actions = [e["action"] for e in c.get(f"/api/projects/{pid}/audit", headers=h).json()]
check("evento generacion_informe auditado", "generacion_informe_cualitativo" in actions, str(actions))

# acceso cruzado al progreso -> 404
r2 = c.post("/auth/signup", json={"email": "f3b@x.cl", "password": "clave12345"})
hb = {"Authorization": f"Bearer {r2.json()['token']}"}
r = c.get(f"/api/projects/{pid}/report/progress", headers=hb)
check("progreso cruzado -> 404", r.status_code == 404, str(r.status_code))

print()
print("RESULTADO:", "TODO OK" if not FAILS else f"{len(FAILS)} FALLAS: {FAILS}")
sys.exit(1 if FAILS else 0)
