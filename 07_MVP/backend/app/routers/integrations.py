"""Integraciones Qualtrics y Google Forms (movido tal cual desde main.py)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app import store
from app.auth import get_current_user
from app.database import get_db
from app.deps import _get_or_404
from app.models import User
from app.routers.projects import _create_project_from_df
from app.services.integrations import credentials, google_forms, qualtrics
from app.services.integrations.base import IntegrationError

router = APIRouter()


# ---------- Integraciones: Qualtrics y Google Forms ----------
# Arquitectura: app/services/integrations/* — cada fuente entrega un DataFrame
# y desemboca en _create_project_from_df (el mismo camino que subir un archivo).

class QualtricsCredentials(BaseModel):
    api_token: str
    datacenter: str


class QualtricsImportBody(BaseModel):
    name: str
    survey_id: str
    survey_name: str = ""
    marco_teorico: str = ""
    text_column: str = ""
    template: str = ""


class GoogleFormsImportBody(BaseModel):
    name: str
    sheet_url: str
    marco_teorico: str = ""
    text_column: str = ""
    template: str = ""


def _qualtrics_config(user: User) -> dict:
    cfg = (user.integrations or {}).get("qualtrics")
    if not cfg or not cfg.get("token_enc"):
        raise HTTPException(400, "No hay credenciales de Qualtrics configuradas. Ingrésalas primero.")
    try:
        token = credentials.decrypt(cfg["token_enc"])
    except IntegrationError as e:
        raise HTTPException(400, str(e))
    return {"api_token": token, "datacenter": cfg.get("datacenter", "")}


@router.get("/api/integrations/qualtrics/credentials")
def qualtrics_credentials_status(user: User = Depends(get_current_user)):
    """La UI solo sabe si hay credenciales y el datacenter; el token jamás sale del backend."""
    cfg = (user.integrations or {}).get("qualtrics") or {}
    return {"configured": bool(cfg.get("token_enc")), "datacenter": cfg.get("datacenter", "")}


@router.put("/api/integrations/qualtrics/credentials")
def qualtrics_save_credentials(body: QualtricsCredentials, user: User = Depends(get_current_user)):
    if not body.api_token.strip() or not body.datacenter.strip():
        raise HTTPException(400, "API Token y Datacenter ID son obligatorios.")
    get_db().users.update_one({"_id": user.id}, {"$set": {"integrations.qualtrics": {
        "token_enc": credentials.encrypt(body.api_token.strip()),
        "datacenter": body.datacenter.strip(),
    }}})
    return {"configured": True, "datacenter": body.datacenter.strip()}


@router.delete("/api/integrations/qualtrics/credentials")
def qualtrics_delete_credentials(user: User = Depends(get_current_user)):
    get_db().users.update_one({"_id": user.id}, {"$unset": {"integrations.qualtrics": ""}})
    return {"configured": False}


@router.get("/api/integrations/qualtrics/surveys")
def qualtrics_surveys(user: User = Depends(get_current_user)):
    cfg = _qualtrics_config(user)
    try:
        return qualtrics.list_surveys(cfg["api_token"], cfg["datacenter"])
    except IntegrationError as e:
        raise HTTPException(400, str(e))


@router.post("/api/projects/from-qualtrics")
def create_project_from_qualtrics(body: QualtricsImportBody, user: User = Depends(get_current_user)):
    cfg = _qualtrics_config(user)
    try:
        df = qualtrics.fetch_responses({**cfg, "survey_id": body.survey_id})
    except IntegrationError as e:
        raise HTTPException(400, str(e))
    result = _create_project_from_df(
        df, body.name, body.marco_teorico, body.text_column, body.template, user,
        source_detail={"fuente": "qualtrics", "encuesta_id": body.survey_id,
                       "encuesta": body.survey_name or body.survey_id},
    )
    project = store.get_project(result["id"], user.org_id)
    store.log_event(project, "sistema", "importacion_qualtrics", {
        "encuesta_id": body.survey_id, "encuesta": body.survey_name or body.survey_id,
        "n_respuestas": result["n_responses"], "usuario": user.email,
    })
    return result


@router.post("/api/projects/from-google-forms")
def create_project_from_google_forms(body: GoogleFormsImportBody, user: User = Depends(get_current_user)):
    try:
        df = google_forms.fetch_responses({"sheet_url": body.sheet_url})
    except IntegrationError as e:
        raise HTTPException(400, str(e))
    result = _create_project_from_df(
        df, body.name, body.marco_teorico, body.text_column, body.template, user,
        source_detail={"fuente": "google_forms", "planilla": body.sheet_url},
    )
    project = store.get_project(result["id"], user.org_id)
    store.log_event(project, "sistema", "importacion_google_forms", {
        "planilla": body.sheet_url, "n_respuestas": result["n_responses"], "usuario": user.email,
    })
    return result
