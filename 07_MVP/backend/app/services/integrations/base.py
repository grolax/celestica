"""
Interfaz común de integraciones de importación.

Contrato: cada fuente implementa `fetch_responses(config) -> pandas.DataFrame`.
La creación de proyecto ya trabaja sobre un DataFrame (igual que un CSV/XLSX
subido a mano), así que agregar una fuente nueva es solo implementar esta
función y registrarla. Importación puntual, no sincronización continua.

Errores: levantar IntegrationError con un mensaje apto para mostrar al
usuario (token inválido, encuesta sin respuestas, permisos insuficientes...).
"""
from __future__ import annotations


class IntegrationError(Exception):
    """Error de integración con mensaje apto para la UI."""
    pass
