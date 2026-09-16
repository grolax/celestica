# Prompt para Fable 5: Refactorizar SoftInsight V2 — Arquitectura Multi-Prompt

**CONTEXTO GENERAL**

SoftInsight es una plataforma de análisis cualitativo para universidades. Actualmente genera informes cualitativos llamando UNA SOLA VEZ a Claude Sonnet con todo el contexto al mismo tiempo. Esto es lento y caro.

**CAMBIO SOLICITADO**

Refactorizar `app/services/thematic.py` para que la generación del informe cualitativo se divida en 3 prompts secuenciales, cada uno optimizado para Fable 5, en lugar de un único prompt monolítico.

**NUEVA ARQUITECTURA**

El nuevo flujo será:

```
Usuario hace click "Generar Informe"
    ↓
[PROMPT 1] — Análisis contextual integrado
  • Procesa CADA respondente (iterable)
  • VE toda la información del respondente: preguntas cerradas + respuesta abierta
  • Extrae subtemas CON CONTEXTO (sabe qué herramienta usa, frecuencia, etc.)
  • Output: análisis individual + cluster assignment
    ↓
[PROMPT 2] — Síntesis y agregación (UNA llamada)
  • Recibe todos los análisis individuales
  • Agrupa por cluster
  • Cuenta prevalencia por metadata (rol, herramienta, frecuencia)
  • Selecciona citas representativas
  • Output: clusters sintetizados + citas
    ↓
[PROMPT 3] — Redacción del informe (Fable 5, UNA llamada)
  • Recibe clusters sintetizados
  • Redacta informe integrado: números + citas + análisis
  • Cero eufemismos, neutralidad radical
  • Output: informe final (texto markdown)
```

---

## ARQUITECTURA TÉCNICA DETALLADA

### PASO 1: Modificar estructura de datos en main.py

En `app/main.py`, la función `generate_report()` (línea 716) debe cambiar.

**Cambio de firma:**
```python
# ACTUAL (línea 748):
report = thematic.generate_qualitative_report(
    marco_teorico=proj["marco_teorico"],
    categories=validated,
    codings=proj["codings"],
    responses=proj["responses"],
    lexical_data=proj.get("lexical"),
    progress_cb=progress_cb,
)

# NUEVO:
report = thematic.generate_qualitative_report_v2(
    survey_id=proj["id"],
    marco_teorico=proj["marco_teorico"],
    categories=validated,
    codings=proj["codings"],
    responses=proj["responses"],
    columns=proj["columns"],  # NUEVO: lista de columnas (preguntas cerradas)
    text_column=proj["text_column"],  # cuál es la columna de pregunta abierta
    lexical_data=proj.get("lexical"),
    progress_cb=progress_cb,
)
```

Mantén la función antigua `generate_qualitative_report()` como fallback, pero úsala solo si el usuario explícitamente lo elige (opción de "modo rápido" en UI).

---

### PASO 2: Refactorizar thematic.py

**Crear 3 funciones nuevas en `app/services/thematic.py`:**

#### Función A: `_analyze_respondent_v2()`

```python
def _analyze_respondent_v2(
    respondent_id: str,
    open_response_text: str,
    closed_responses: dict,  # {"q1": "Sí", "q2": "ChatGPT", "q3": "Diario"}
    respondent_metadata: dict,  # {"role": "docente", "faculty": "Ingeniería"}
    marco_teorico: str,
) -> dict:
    """
    Analiza UNA respuesta de pregunta abierta EN CONTEXTO de todas sus respuestas cerradas.
    
    Input:
    - respondent_id: "R_001"
    - open_response_text: "Las uso para..."
    - closed_responses: {"q_1": "Sí", "q_2": "ChatGPT", "q_3": "Diariamente"}
    - respondent_metadata: {"role": "docente", "faculty": "Ingeniería", ...}
    - marco_teorico: contexto del proyecto
    
    Output:
    {
        "respondent_id": "R_001",
        "is_valid": true,
        "subtopics": [
            {
                "subtopic_name": "generación_de_ejercicios",
                "context_connection": {
                    "closed_question": "q_2",
                    "closed_answer": "ChatGPT",
                    "relevance": "herramienta específica usada para esta tarea"
                },
                "evidence_quote": "[cita textual exacta]",
                "analysis_cluster": "generación_de_ejercicios:ChatGPT_diario"
            }
        ],
        "respondent_profile": "Docente, Ingeniería, ChatGPT diario, <6 meses",
        "metadata_snapshot": {"role": "docente", "primary_tool": "ChatGPT", ...}
    }
    """
    # Implementación:
    # 1. Llamar a Fable 5 con PROMPT 1 (especificado abajo)
    # 2. Parsear JSON output
    # 3. Retornar dict estructurado
```

**Parámetros de Fable para `_analyze_respondent_v2()`:**
- `model`: "claude-fable-5"
- `max_tokens`: 1500
- System prompt + instructions: ver sección **PROMPTS** abajo

---

#### Función B: `_synthesize_clusters_v2()`

```python
def _synthesize_clusters_v2(
    survey_id: str,
    all_respondent_analyses: list[dict],  # salida de Prompt 1 x N respondentes
    total_respondents: int,
    marcos_teorico: str,
) -> dict:
    """
    Agrega todos los análisis individuales en clusters.
    
    Input: lista de dicts de _analyze_respondent_v2()
    
    Output:
    {
        "survey_id": "...",
        "respondents_analyzed": {"total": 127, "valid": 115, "rejected": 12, ...},
        "clusters": [
            {
                "cluster_name": "generación_de_ejercicios:ChatGPT_diario",
                "prevalence": {"count": 34, "percentage": 29.6},
                "breakdown_by_metadata": {
                    "by_role": {"docente": 28, "investigador": 6},
                    "by_tool": {"ChatGPT": 32, "Claude": 2}
                },
                "representative_quotes": [
                    {"quote": "...", "respondent_profile": "Docente, Ing.", "rationale": "central"}
                ]
            }
        ]
    }
    """
    # Implementación:
    # 1. Llamar a Fable 5 con PROMPT 2 (especificado abajo)
    # 2. Parsear JSON
    # 3. Retornar dict estructurado
```

**Parámetros de Fable para `_synthesize_clusters_v2()`:**
- `model`: "claude-fable-5"
- `max_tokens`: 3000
- System prompt + instructions: ver sección **PROMPTS** abajo

---

#### Función C: `_write_report_v2()`

```python
def _write_report_v2(
    clusters_analysis: dict,  # output de _synthesize_clusters_v2()
    marco_teorico: str,
) -> str:
    """
    Redacta el informe cualitativo integrado.
    
    Input: clusters_analysis dict con todos los clusters sintetizados
    Output: texto markdown del informe (sin JSON, texto limpio)
    """
    # Implementación:
    # 1. Llamar a Fable 5 con PROMPT 3 (especificado abajo)
    # 2. Retornar texto markdown
```

**Parámetros de Fable para `_write_report_v2()`:**
- `model`: "claude-fable-5"
- `max_tokens`: 4000
- System prompt + instructions: ver sección **PROMPTS** abajo

---

#### Función D: `generate_qualitative_report_v2()` (orquestador)

```python
def generate_qualitative_report_v2(
    survey_id: str,
    marco_teorico: str,
    categories: list[dict],
    codings: dict,
    responses: list[dict],
    columns: list[str],
    text_column: str,
    lexical_data: Optional[dict],
    progress_cb=None,
) -> str:
    """
    Orquesta el flujo completo: Prompt 1 → Prompt 2 → Prompt 3.
    
    Retorna texto del informe (markdown).
    """
    # Pseudocódigo:
    
    # PASO 1: Preparar data por respondente
    # Mapear responses a estructura: cada response tiene su ID, su texto abierto, 
    # sus respuestas cerradas (meta), su metadata (role, faculty, etc.)
    responses_structured = []
    for r in responses:
        responses_structured.append({
            "respondent_id": r["id"],
            "open_response": r["text"],
            "closed_responses": r.get("meta", {}),  # preguntas cerradas como dict
            "metadata": {
                "role": r.get("meta", {}).get("role", ""),
                "faculty": r.get("meta", {}).get("faculty", ""),
                # ... otros metadatos
            }
        })
    
    # PASO 2: Llamar PROMPT 1 para cada respondente (con progress)
    all_analyses = []
    for i, resp_struct in enumerate(responses_structured):
        analysis = _analyze_respondent_v2(
            respondent_id=resp_struct["respondent_id"],
            open_response_text=resp_struct["open_response"],
            closed_responses=resp_struct["closed_responses"],
            respondent_metadata=resp_struct["metadata"],
            marco_teorico=marco_teorico,
        )
        all_analyses.append(analysis)
        
        if progress_cb:
            progress_cb(
                f"Analizando respondente {i+1}/{len(responses_structured)}"
            )
    
    # PASO 3: Llamar PROMPT 2 (agregación)
    clusters_result = _synthesize_clusters_v2(
        survey_id=survey_id,
        all_respondent_analyses=all_analyses,
        total_respondents=len(responses),
        marco_teorico=marco_teorico,
    )
    
    if progress_cb:
        progress_cb("Sintetizando clusters...")
    
    # PASO 4: Llamar PROMPT 3 (redacción)
    report = _write_report_v2(
        clusters_analysis=clusters_result,
        marco_teorico=marco_teorico,
    )
    
    if progress_cb:
        progress_cb("Informe completado.")
    
    return report
```

---

### PASO 3: Actualizar prompt_store.py

En `app/prompt_store.py`, agregar los 3 nuevos prompts en el diccionario `DEFAULT_PROMPTS`:

```python
"analyze_respondent_v2": {
    "system": "[PROMPT 1 SYSTEM - ver abajo]",
    "instructions": "[PROMPT 1 INSTRUCTIONS - ver abajo]",
},
"synthesize_clusters_v2": {
    "system": "[PROMPT 2 SYSTEM - ver abajo]",
    "instructions": "[PROMPT 2 INSTRUCTIONS - ver abajo]",
},
"write_report_v2": {
    "system": "[PROMPT 3 SYSTEM - ver abajo]",
    "instructions": "[PROMPT 3 INSTRUCTIONS - ver abajo]",
},
```

---

## PROMPTS PARA FABLE 5

### PROMPT 1: Análisis Contextual Integrado

**System:**
```
SISTEMA: Eres un analista de datos cualitativos especializado en investigación educativa. 
Tu tarea es analizar respuestas de encuestas abiertas INTEGRÁNDOLAS CON TODO EL CONTEXTO 
disponible del respondente. No haces síntesis a nivel población — eso viene después.
Enfócate en UNA respuesta, pero con toda su información de contexto.
```

**Instructions:**
```
TAREA PRINCIPAL:
Analiza la respuesta abierta del respondente conectándola explícitamente con sus respuestas 
de preguntas cerradas. El objetivo es identificar SUBTEMAS EN CONTEXTO.

ENTRADA:
- Pregunta abierta: {open_response_text}
- Respuesta del respondente: [será inserida aquí]
- Contexto del respondente (preguntas cerradas): {closed_responses_json}
- Metadata: {respondent_metadata_json}
- Marco teórico: {marco_teorico}

TAREAS:

A. VALIDACIÓN
¿La respuesta es sustantiva y usable?
Marca como "rejected" si: está vacía, es "N/A", "Nada", "No sé", no responde la pregunta (off-topic), o es puro ruido.
Si es usable, continúa.

B. IDENTIFICACIÓN DE SUBTEMAS (CON CONTEXTO)
- Identifica 1–3 subtemas principales
- Para cada subtema:
  a) Nombra neutral y específico (ej: "generación_de_ejercicios")
  b) Busca conexiones EXPLÍCITAS con datos cerrados (ej: "usa ChatGPT" + "diariamente")
  c) Extrae cita TEXTUAL (exacta, sin editar)

C. ASIGNACIÓN A CLUSTER
Crea nombre de cluster: {subtema}:{contexto_clave}
Ejemplo: "generación_de_ejercicios:ChatGPT_diario"

D. PERFIL
Resumen en 1 línea: "{rol}, {faculty}, usa {herramienta} {frecuencia}, {experiencia}"

SALIDA (JSON):
{
  "respondent_id": "string",
  "is_valid": boolean,
  "rejection_reason": "string o null",
  "subtopics": [
    {
      "subtopic_name": "string",
      "context_connection": {
        "closed_question_id": "string",
        "closed_question_label": "string",
        "closed_answer": "string",
        "relevance_explanation": "string"
      },
      "evidence_quote": "string (exacta)",
      "analysis_cluster": "string"
    }
  ],
  "respondent_profile_line": "string",
  "metadata_snapshot": {"role": "string", "primary_tool": "string", ...}
}

REGLAS:
- Solo hechos conectados a datos
- Citas SIN EDITORIALIZAR: exactas
- Sin eufemismos ni adjetivos editorialistas
```

---

### PROMPT 2: Síntesis y Agregación

**System:**
```
SISTEMA: Eres un agregador de análisis cualitativos. Tu tarea es SINTETIZAR todos 
los análisis individuales en clusters coherentes, identificar patrones, variaciones 
y seleccionar citas representativas.
```

**Instructions:**
```
TAREA:
Procesa todos los análisis individuales (output de Prompt 1 x N respondentes) 
y crea un resumen estructurado por cluster.

ENTRADA:
Array de análisis individuales: {all_respondent_analyses_json}
Total de respondentes: {total_respondents}
Marco teórico: {marco_teorico}

PASOS:

A. AGRUPACIÓN POR CLUSTER
- Agrupa todos los subtopics por su "analysis_cluster"
- Para cada cluster: cuenta prevalencia, desglose por metadata

B. CONTAR PREVALENCIA
- total_count: cuántos respondentes mencionaron
- total_percentage: (count / total_respondents) × 100
- breakdown_by_metadata: desglosa por rol, herramienta, frecuencia

C. SELECCIONAR CITAS (2–3 por cluster)
- Una cita "central" (típica)
- Una cita "con matiz" (perspectiva diferente)
- Opcional: una cita menos común

D. VARIACIONES INTERNAS
Si hay patrones dentro del cluster, documéntalos
Ej: "80% usa ChatGPT, 20% usa Claude"

SALIDA (JSON):
{
  "respondents_analyzed": {
    "total": number,
    "valid": number,
    "rejected": number,
    "rejection_breakdown": {"empty": number, "off_topic": number, ...}
  },
  "clusters": [
    {
      "cluster_name": "string",
      "prevalence": {"count": number, "percentage": number},
      "breakdown_by_metadata": {
        "by_role": {"docente": number, ...},
        "by_tool": {"ChatGPT": number, ...}
      },
      "representative_quotes": [
        {"quote": "string", "respondent_profile": "string", "rationale": "string"}
      ],
      "internal_variations": [
        {"variation": "string", "prevalence_note": "string"}
      ]
    }
  ]
}

REGLAS:
- Cuenta SIN INTERPRETACIÓN
- Citas SIN EDITORIALIZAR: exactas
- Variaciones EXPLÍCITAS
- No elimines clusters pequeños
```

---

### PROMPT 3: Redacción del Informe

**System:**
```
SISTEMA: Eres un redactor de informes cualitativos. Tu tarea es convertir clusters 
sintetizados en un INFORME INTEGRADO que sea neutral, basado en datos, y respaldado 
por citas textuales.
```

**Instructions:**
```
TAREA:
Redacta un informe estructurado, integrado, neutral, sin eufemismos.

ENTRADA:
Análisis de clusters sintetizados: {clusters_analysis_json}
Marco teórico: {marco_teorico}

ESTRUCTURA DEL INFORME:

1. RESUMEN EJECUTIVO (1 párrafo)
   - Cuántas respuestas se analizaron
   - Cuántos clusters identificados
   - Rango de prevalencia

2. ANÁLISIS POR CLUSTER (1–2 párrafos cada uno, ordenado por prevalencia)
   Cada cluster tiene:
   - Párrafo A: Prevalencia pura + desglose por metadata
   - Párrafo B: 2–3 citas textuales
   - Párrafo C (opcional): Variaciones internas

3. SÍNTESIS INTEGRADA (1 párrafo)
   - Herramientas dominantes
   - Perfiles de uso por rol
   - Patrones de frecuencia

REGLAS DE NEUTRALIDAD RADICAL:
✅ HACER:
- "47 de 115 respondentes mencionó X" (números)
- "El promedio fue 3.2/5" (datos puros)
- "Un docente señaló: '[cita]'" (sin adjetivos)

❌ NO HACER:
- "Significativamente más" → "47 vs. 23"
- "Un hallazgo importante" → "Se identificó que..."
- "Desafío emergente" → nombra literalmente qué es
- Adjetivos sin soporte: "grave", "urgente", "importante"
- Verbos editorialistas: "reclaman", "exigen" → "reportan", "mencionan"

LARGO:
- 4–8 párrafos totales
- 100–180 palabras por párrafo
- Máximo 1500 palabras totales

SALIDA:
Texto markdown plano (NO JSON). 
Usa # para secciones, ## para subsecciones, ** para énfasis en números.
```

---

## CONSIDERACIONES FINALES

### Logging y Auditoría
- Mantén los `store.log_event()` en `generate_report()` (main.py)
- Agrega eventos de cada paso del flujo multi-prompt

### Rollback
- Mantén la función antigua `generate_qualitative_report()` disponible
- Si V2 falla, ofrece fallback a V1 (pero documenta en UI que es "modo rápido")

### Testing
- Prueba con encuesta pequeña (50 respondentes)
- Verifica que Prompt 1 capture contexto (herramientas + frecuencia conectadas)
- Verifica que Prompt 2 agregue sin perder variaciones
- Verifica que Prompt 3 redacte sin eufemismos

### Modelo
- Todas las llamadas: `claude-fable-5` (no Sonnet, no Haiku)
- Excepción: si quieres, Prompt 1 podría ser Sonnet para ahorrar si N respondentes > 500

### Variable de entorno
Agregar opcional en .env:
```
CLAUDE_MODEL_REPORT_V2=claude-fable-5
```

---

## Archivos a Modificar

1. `app/main.py` — cambiar línea 748 en `generate_report()` 
2. `app/services/thematic.py` — agregar 4 funciones nuevas
3. `app/prompt_store.py` — agregar 3 prompts nuevos
4. `.env` — variable `CLAUDE_MODEL_REPORT_V2` (opcional)

No modificar: `models.py`, `database.py`, `store.py` (backward compatible).
