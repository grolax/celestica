# Estado del desarrollo

Archivo mantenido por el agente `supervisor`. Una línea por entrada.

## Hecho

| Tarea | Lado | Requerimientos | Fecha | Rama |
| --- | --- | --- | --- | --- |
| — | — | Línea base: MVP v1.1 (ver `07_MVP/COMO_FUNCIONA.md`) | 2026-10 | main |

## En curso

(nada)

## Bloqueado / requiere decisión del usuario

(nada)

## Deuda técnica detectada

- `backend/app/main.py` concentra todos los endpoints (~950 líneas); separar en routers (RNF-17).
- Progreso de codificación e informe vive en memoria; se pierde si el servidor se reinicia (RNF-12).
- Stopwords del análisis léxico fijas y orientadas a educación superior chilena (RF-14).
