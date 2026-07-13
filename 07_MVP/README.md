# SoftInsight v1.1

Plataforma de análisis cualitativo asistido por IA para organizaciones que analizan respuestas abiertas (universidades, estudios de mercado, RR.HH., sector público, salud): importar datos → análisis léxico → análisis temático asistido por Claude (con validación humana) → trazabilidad → informe cualitativo → **exportación PDF/DOCX/CSV/XLSX**.

**Estado v1.1:** multi-tenant con autenticación JWT sobre **MongoDB**, UI profesional (frontend organizado por features), **12 plantillas de marcos teóricos en 5 industrias**, **importación desde Qualtrics y Google Forms**, informe cualitativo con **progreso de generación en tiempo real (streaming)**, comentarios colaborativos y auditoría completa.

## Requisitos

- Python 3.9+
- Node.js 18+
- **MongoDB Community** (local; Atlas para producción)
- API key de Anthropic (solo para el análisis temático e informe; el léxico funciona sin ella)

## Instalación

### 1. MongoDB (macOS, vía Homebrew)

```bash
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community   # queda corriendo en localhost:27017
```

> Verificar: `mongosh --eval "db.runCommand({ping: 1})"` debe responder `ok: 1`.
> Para detenerlo: `brew services stop mongodb-community`.

### 2. Backend

```bash
cd 07_MVP/backend
pip install -r requirements.txt
cp .env.example .env        # editar: ANTHROPIC_API_KEY y SECRET_KEY (firma de JWT)
uvicorn app.main:app --reload --port 8000
```

La base `softinsight` y sus índices se crean solos al arrancar. La conexión se controla con `MONGODB_URI` (default `mongodb://localhost:27017/softinsight`). **Migrar a MongoDB Atlas = cambiar esa variable**; el código no cambia.

#### Migrar datos de la v1.0 (SQLite)

Si tienes un `backend/softinsight.db` de la versión anterior:

```bash
cd 07_MVP/backend
python scripts/migrate_sqlite_to_mongo.py    # idempotente: correrlo 2 veces no duplica
```

Imprime un resumen de usuarios, proyectos y eventos de auditoría migrados.

### 3. Frontend (en otra terminal)

```bash
cd 07_MVP/frontend
npm install
npm run dev
```

Abrir **http://localhost:5173** → crear cuenta → nuevo proyecto.

## Orígenes de datos para un proyecto

1. **Subir archivo** — CSV o XLSX con una columna de respuestas abiertas (detección automática de la columna de texto).
2. **Qualtrics** — con API Token + Datacenter ID (se guardan **cifrados** en el servidor, nunca en el navegador): listar encuestas → elegir → importar.
3. **Google Forms** — vía la planilla de respuestas de Google Sheets compartida como "Cualquiera con el enlace puede ver". (OAuth completo de Google quedó documentado como iteración futura; esta vía cubre la importación puntual sin fricción.)

Toda importación queda auditada (`importacion_qualtrics` / `importacion_google_forms` con encuesta/planilla y n° de respuestas).

## Plantillas de marcos teóricos (12, por industria)

| Industria | Plantillas |
| --- | --- |
| Educación Superior | Evaluación Docente (CNA) · Satisfacción Estudiantil · Acreditación Institucional (CNA) |
| Estudios de Mercado | Satisfacción de Clientes (NPS) · Percepción de Marca · Investigación de Producto/Concepto |
| Organizaciones y B2B | Clima y Cultura Organizacional · Feedback de Empleados (pulso/salida) · Voz del Cliente B2B |
| Sector Público | Consultas Ciudadanas · Evaluación de Servicios Públicos |
| Salud | Experiencia de Pacientes |

Cada plantilla trae marco teórico redactado + 4–5 categorías con criterios de inclusión **y exclusión**. Las categorías entran con status `propuesta`: la validación humana es parte del método.

## Flujo de demo (guion sugerido, ~10 min)

1. **Signup / Login**: cada usuario ve solo sus proyectos (multi-tenant real).
2. **Nuevo proyecto**: subir `data/dataset_demo_evaluacion_docente.csv` (320 respuestas sintéticas) o importar desde Qualtrics/Google Forms. Elegir plantilla (agrupadas por industria).
3. **Dashboard**: estado del análisis paso a paso, métricas y distribución de confianza.
4. **Análisis léxico**: frecuencias, bigramas, sentimiento con evidencia. Corre en segundos, método transparente.
5. **Libro de códigos**: validar las categorías de plantilla o pedir propuestas a la IA. **La IA propone, el humano decide.**
6. **Codificación**: barra de progreso por lotes; justificación y confianza por asignación.
7. **Trazabilidad**: respuesta → categoría → justificación → fuente, con filtros. **Diferenciador de auditoría.**
8. **Informe**: generación con **barra de progreso real** (streaming: se ve qué sección está redactando).
9. **Exportar**: PDF formal, Word editable, CSV/Excel.
10. **Auditoría**: todo evento (humano o IA) registrado con timestamp. "Nada es caja negra."

## Arquitectura

```
backend/
  app/main.py               # API REST (auth-protegida; proyectos, análisis, integraciones, exportación)
  app/auth.py               # JWT: signup/login/me + dependency get_current_user
  app/database.py           # MongoDB vía pymongo (MONGODB_URI; índices en init_db)
  app/models.py             # User (dataclass) + mapeo de documentos
  app/store.py              # persistencia multi-tenant + audit log ($set/$push parciales)
  app/templates.py          # 12 plantillas de marcos teóricos en 5 industrias
  app/services/lexical.py   # Capa 1: frecuencias, bigramas, co-ocurrencias, sentimiento
  app/services/thematic.py  # Capa 2: Claude API (con streaming para el informe)
  app/services/export.py    # PDF (reportlab + matplotlib), DOCX (python-docx), CSV/XLSX
  app/services/integrations/  # base (interfaz DataFrame) + qualtrics + google_forms + credentials (cifrado)
  scripts/migrate_sqlite_to_mongo.py  # migración v1.0 → v1.1, idempotente
  tests/                    # verificación con mongomock + IA simulada (no gastan API)
frontend/
  src/App.tsx               # router (rutas protegidas por sesión)
  src/shared/               # api/client.ts, components (Button/Card/Input/Table), layout, hooks
  src/shared/hooks/         # useAsync, usePolling, useDownload
  src/features/auth/        # useAuth, LoginPage
  src/features/projects/    # ProjectList, NewProject (3 orígenes), ProjectView, Dashboard, useProjectData
  src/features/analysis/    # lexical/ codebook/ coding/ traceability/ report/ audit/
  src/features/export/      # ExportReport
  src/features/integrations/# QualtricsSection + api
  src/features/settings/    # cuenta, importar demo, panel de prompts
  src/styles/globals.css    # paleta: blanco/crema + celeste #0099CC, tipografía Inter
data/
  dataset_demo_evaluacion_docente.csv
```

Colecciones en MongoDB: `users` (email único), `projects` (documento completo del proyecto, indexado por `user_id`), `audit_events` (copia plana consultable, indexada por `project_id`). Las operaciones puntuales (validar categoría, comentar, re-codificar, guardar informe) usan actualizaciones parciales `$set`/`$push`: no reescriben las respuestas del proyecto.

## Variables de entorno (backend/.env)

| Variable | Uso | Default |
| --- | --- | --- |
| `ANTHROPIC_API_KEY` | Análisis temático e informe | — (requerida para IA) |
| `SECRET_KEY` | Firma de JWT + cifrado de credenciales de integraciones | dev (cambiar en producción) |
| `MONGODB_URI` | Conexión a MongoDB (local o Atlas) | `mongodb://localhost:27017/softinsight` |
| `ADMIN_PASSWORD` | Panel de prompts metodológicos | `softinsight2026` |
| `CLAUDE_MODEL` | Modelo de IA | `claude-sonnet-4-6` |

## Costo estimado de Claude API

Con el dataset demo (320 respuestas): 1 llamada de propuesta de categorías + ~13 llamadas de codificación por lotes de 25 + 1 informe (streaming). Orden de magnitud: < US$1 por corrida completa con Sonnet.

## Pendiente para siguientes iteraciones

- OAuth completo de Google (hoy: importación vía planilla pública, decisión documentada)
- Sincronización continua con Qualtrics (hoy: importación puntual)
- Colaboración en tiempo real (múltiples codificadores concurrentes)
- Comparativas entre ciclos / trends
- Emails de confirmación y recuperación de contraseña
- Suite Playwright de UI (los tests de backend ya están en `backend/tests/`)
