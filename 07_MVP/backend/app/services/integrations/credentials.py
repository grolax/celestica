"""
Cifrado de credenciales de integraciones (Fernet/AES sobre SECRET_KEY).

Las credenciales (ej: API Token de Qualtrics) se guardan cifradas en el
documento del usuario en Mongo y NUNCA se envían al navegador: la UI solo
sabe si están configuradas y para qué datacenter.
"""
from __future__ import annotations

import base64
import hashlib
import os

from cryptography.fernet import Fernet, InvalidToken

from app.services.integrations.base import IntegrationError

_SECRET = os.environ.get("SECRET_KEY", "dev-secret-cambiar-en-produccion")


def _fernet() -> Fernet:
    key = base64.urlsafe_b64encode(
        hashlib.sha256(("softinsight-credentials:" + _SECRET).encode()).digest()
    )
    return Fernet(key)


def encrypt(value: str) -> str:
    return _fernet().encrypt(value.encode()).decode()


def decrypt(value: str) -> str:
    try:
        return _fernet().decrypt(value.encode()).decode()
    except (InvalidToken, ValueError):
        raise IntegrationError(
            "No se pudieron descifrar las credenciales guardadas (¿cambió SECRET_KEY?). "
            "Vuelve a ingresarlas."
        )
