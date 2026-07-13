"""Fase 5: integraciones Qualtrics + Google Forms con requests simulado."""
import io
import json
import sys
import zipfile

import mongomock

from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import database
database._client = mongomock.MongoClient()

from fastapi.testclient import TestClient
from app.main import app
from app.services.integrations import google_forms, qualtrics

FAILS = []
def check(name, cond, extra=""):
    print(("PASS  " if cond else "FAIL  ") + name + (f"  [{extra}]" if extra and not cond else ""))
    if not cond:
        FAILS.append(name)

# ---------- mock de requests ----------
class FakeResponse:
    def __init__(self, status=200, jdata=None, content=b"", ctype="application/json"):
        self.status_code = status
        self._j = jdata
        self.content = content
        self.headers = {"Content-Type": ctype}
        self.text = json.dumps(jdata) if jdata else ""
        self.ok = 200 <= status < 300
    def json(self):
        return self._j

QUALTRICS_CSV = (
    "QID1,QID2\n"                                # fila header=0 (ids)
    "Comentario,Edad\n"                          # header=1 (texto pregunta) ← usado
    '{"ImportId":"QID1"},{"ImportId":"QID2"}\n'  # metadata (se descarta)
    "El servicio fue excelente y rapido,34\n"
    "Muy lenta la atencion en la sucursal,51\n"
    "Todo bien pero el precio es alto,28\n"
)
def make_zip(csv_text):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("export.csv", csv_text)
    return buf.getvalue()

STATE = {"token_ok": "TOK123"}

def fake_get(url, headers=None, timeout=None, allow_redirects=True):
    # Qualtrics
    if "qualtrics.com" in url:
        if (headers or {}).get("X-API-TOKEN") != STATE["token_ok"]:
            return FakeResponse(401)
        if url.endswith("/surveys"):
            return FakeResponse(jdata={"result": {"elements": [
                {"id": "SV_1", "name": "NPS Clientes 2026"},
                {"id": "SV_2", "name": "Clima Interno"}], "nextPage": None}})
        if "/export-responses/PROG" in url:
            return FakeResponse(jdata={"result": {"status": "complete", "fileId": "FILE1"}})
        if "/FILE1/file" in url:
            return FakeResponse(content=make_zip(QUALTRICS_CSV))
    # Google Sheets
    if "docs.google.com" in url:
        if "PRIVADA" in url:
            return FakeResponse(status=200, content=b"<html>login</html>", ctype="text/html")
        if "VACIA" in url:
            return FakeResponse(content=b"respuesta\n", ctype="text/csv")
        return FakeResponse(content=(
            b"Marca temporal,Que opinas del taller?\n"
            b"2026-07-01,Fue muy util y bien organizado el taller completo\n"
            b"2026-07-02,Falto tiempo para la parte practica del taller\n"
        ), ctype="text/csv")
    return FakeResponse(404)

def fake_post(url, headers=None, json=None, timeout=None):
    if "qualtrics.com" in url and url.endswith("/export-responses"):
        if (headers or {}).get("X-API-TOKEN") != STATE["token_ok"]:
            return FakeResponse(401)
        return FakeResponse(jdata={"result": {"progressId": "PROG"}})
    return FakeResponse(404)

qualtrics.requests.get = fake_get
qualtrics.requests.post = fake_post
google_forms.requests.get = fake_get

c = TestClient(app, raise_server_exceptions=False)
r = c.post("/auth/signup", json={"email": "f5@x.cl", "password": "clave12345"})
h = {"Authorization": f"Bearer {r.json()['token']}"}

# ---- credenciales ----
r = c.get("/api/integrations/qualtrics/credentials", headers=h)
check("status inicial no configurado", r.json() == {"configured": False, "datacenter": ""}, r.text)

r = c.get("/api/integrations/qualtrics/surveys", headers=h)
check("listar sin credenciales -> 400", r.status_code == 400, r.text)

r = c.put("/api/integrations/qualtrics/credentials", headers=h,
          json={"api_token": "TOK123", "datacenter": "ca1"})
check("guardar credenciales", r.status_code == 200 and r.json()["configured"], r.text)

# token cifrado en la BD (nunca en claro)
doc = database.get_db().users.find_one({"email": "f5@x.cl"})
enc = doc["integrations"]["qualtrics"]["token_enc"]
check("token cifrado en BD", "TOK123" not in enc and len(enc) > 40, enc[:30])
r = c.get("/api/integrations/qualtrics/credentials", headers=h)
check("status no expone token", "token" not in json.dumps(r.json()).lower() or "token_enc" not in r.text, r.text)

# ---- listar encuestas ----
r = c.get("/api/integrations/qualtrics/surveys", headers=h)
check("listar encuestas", r.status_code == 200 and len(r.json()) == 2 and r.json()[0]["name"] == "NPS Clientes 2026", r.text)

# ---- importar desde Qualtrics ----
r = c.post("/api/projects/from-qualtrics", headers=h, json={
    "name": "NPS Q2", "survey_id": "SV_1", "survey_name": "NPS Clientes 2026",
    "template": "satisfaccion_clientes_nps"})
check("importar qualtrics", r.status_code == 200 and r.json()["n_responses"] == 3, r.text)
pid = r.json()["id"]
check("columna de texto detectada", r.json()["text_column"] == "Comentario", r.text)
r = c.get(f"/api/projects/{pid}", headers=h)
check("plantilla NPS aplicada (5 cat)", len(r.json()["categories"]) == 5, str(len(r.json()["categories"])))
audit = c.get(f"/api/projects/{pid}/audit", headers=h).json()
acts = [e["action"] for e in audit]
check("evento importacion_qualtrics", "importacion_qualtrics" in acts, str(acts))
ev = [e for e in audit if e["action"] == "importacion_qualtrics"][0]
check("detalle con encuesta y n", ev["detail"]["encuesta"] == "NPS Clientes 2026" and ev["detail"]["n_respuestas"] == 3, str(ev["detail"]))

# ---- token inválido ----
c.put("/api/integrations/qualtrics/credentials", headers=h, json={"api_token": "MALO", "datacenter": "ca1"})
r = c.get("/api/integrations/qualtrics/surveys", headers=h)
check("token invalido -> 400 con mensaje claro", r.status_code == 400 and "inválido" in r.json()["detail"], r.text)

# ---- borrar credenciales ----
r = c.delete("/api/integrations/qualtrics/credentials", headers=h)
check("borrar credenciales", r.json()["configured"] is False, r.text)

# ---- Google Forms ----
r = c.post("/api/projects/from-google-forms", headers=h, json={
    "name": "Taller Julio", "sheet_url": "https://docs.google.com/spreadsheets/d/ABC123xyz/edit#gid=0"})
check("importar google sheet", r.status_code == 200 and r.json()["n_responses"] == 2, r.text)
pid2 = r.json()["id"]
acts = [e["action"] for e in c.get(f"/api/projects/{pid2}/audit", headers=h).json()]
check("evento importacion_google_forms", "importacion_google_forms" in acts, str(acts))

r = c.post("/api/projects/from-google-forms", headers=h, json={
    "name": "X", "sheet_url": "https://docs.google.com/spreadsheets/d/PRIVADA/edit"})
check("planilla privada -> 400 con instrucciones", r.status_code == 400 and "pública" in r.json()["detail"], r.text)

r = c.post("/api/projects/from-google-forms", headers=h, json={
    "name": "X", "sheet_url": "https://docs.google.com/spreadsheets/d/VACIA/edit"})
check("planilla sin respuestas -> 400", r.status_code == 400 and "respuestas" in r.json()["detail"], r.text)

r = c.post("/api/projects/from-google-forms", headers=h, json={"name": "X", "sheet_url": "https://otracosa.com/x"})
check("URL no-sheets -> 400", r.status_code == 400, r.text)

# conversión de URLs
from app.services.integrations.google_forms import _to_csv_url
check("url normal -> export csv", _to_csv_url("https://docs.google.com/spreadsheets/d/AbC-9_x/edit#gid=42") ==
      "https://docs.google.com/spreadsheets/d/AbC-9_x/export?format=csv&gid=42")
check("url publicada -> pub csv", "pub?output=csv" in _to_csv_url("https://docs.google.com/spreadsheets/d/e/2PACX-abc/pubhtml"))

print()
print("RESULTADO:", "TODO OK" if not FAILS else f"{len(FAILS)} FALLAS: {FAILS}")
sys.exit(1 if FAILS else 0)
