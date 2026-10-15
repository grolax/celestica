# SoftInsight (repositorio celestica)

Antes de cualquier tarea, lee `CONTEXTO_SOFTINSIGHT.md`: describe el producto, el público objetivo, los requerimientos (RF/RNF) y los principios que no se pueden romper.

## Equipo de agentes

- `supervisor`: planifica, escribe órdenes de trabajo en `docs/tareas/`, define contratos en `docs/API_CONTRATOS.md`, delega y revisa. No escribe código de la aplicación.
- `programador-backend`: implementa en `07_MVP/backend/`.
- `programador-frontend`: implementa en `07_MVP/frontend/`.

Forma recomendada de trabajar: iniciar Claude Code como supervisor con `claude --agent supervisor`.

## Archivos de coordinación

- `docs/ESTADO.md`: qué está hecho, en curso y bloqueado.
- `docs/API_CONTRATOS.md`: contrato entre backend y frontend.
- `docs/tareas/`: una orden de trabajo por tarea, con sus revisiones.

## Comandos

- Pruebas del backend: `cd 07_MVP/backend && pytest tests -q`
- Build del frontend: `cd 07_MVP/frontend && npm run build`
- Detalle técnico de lo existente: `07_MVP/COMO_FUNCIONA.md`

## Reglas generales

- Responder en español.
- Solo el supervisor sube ramas a GitHub, y únicamente después de preguntarle al usuario. Nunca push a `main`, nunca `--force`, nunca fusionar pull requests: el merge lo aprueba el usuario.
- Nunca llamar a la API real de Anthropic en pruebas.
- Nunca subir secretos (`.env`) al repositorio.
