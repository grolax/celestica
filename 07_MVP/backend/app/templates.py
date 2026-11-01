"""
Plantillas de marcos teóricos predefinidos, agrupadas por industria.

Los usuarios no parten de cero: eligen una plantilla alineada con procesos
que su organización reconoce (acreditación CNA, NPS, clima organizacional,
consultas ciudadanas...) y la ajustan. Aplicar una plantilla crea el marco
teórico + categorías base (status "propuesta": el analista igual debe
validarlas — la validación humana es parte del método, no un trámite).

Estándar de calidad de cada categoría: definición + criterios de INCLUSIÓN
y de EXCLUSIÓN bien redactados. Los criterios de exclusión son lo que hace
precisa la codificación IA: le dicen al modelo dónde termina una categoría
y empieza la vecina.
"""
from __future__ import annotations

from typing import Optional

FRAMEWORK_TEMPLATES: dict[str, dict] = {

    # ================= EDUCACIÓN SUPERIOR =================

    "evaluacion_docente_cna": {
        "nombre": "Evaluación Docente (marco CNA)",
        "industria": "Educación Superior",
        "palabras_clave": ["profesor", "docente", "clase", "asignatura", "catedra", "ramo", "pedagog", "metodolog", "aprendizaje"],
        "descripcion": "Dimensiones clásicas de la docencia universitaria usadas en procesos de acreditación CNA: dominio disciplinar, metodología, evaluación de aprendizajes y relación pedagógica.",
        "marco_teorico": (
            "Modelo de competencias docentes alineado con criterios CNA: "
            "dominio disciplinar, metodología de enseñanza, evaluación de aprendizajes "
            "y relación pedagógica. Las categorías se anclan a estas cuatro dimensiones."
        ),
        "categorias_default": [
            {"nombre": "Dominio Disciplinar",
             "definicion": "Manejo y actualización de los contenidos de la disciplina que enseña.",
             "criterios_inclusion": "Menciones al conocimiento del profesor sobre la materia, actualización, profundidad, capacidad de responder preguntas complejas.",
             "criterios_exclusion": "Comentarios sobre cómo enseña (eso es Metodología) o sobre el trato (Relación Pedagógica)."},
            {"nombre": "Metodología de Enseñanza",
             "definicion": "Estrategias, técnicas y recursos pedagógicos usados en clases.",
             "criterios_inclusion": "Claridad expositiva, uso de ejemplos, actividades prácticas, materiales, organización de la clase, ritmo.",
             "criterios_exclusion": "Diseño de pruebas o pautas (Evaluación de Aprendizajes)."},
            {"nombre": "Evaluación de Aprendizajes",
             "definicion": "Diseño, aplicación y retroalimentación de las evaluaciones.",
             "criterios_inclusion": "Coherencia prueba-contenido, pautas claras, retroalimentación oportuna, justicia en la corrección.",
             "criterios_exclusion": "Dificultad del ramo en general sin referencia a instrumentos de evaluación."},
            {"nombre": "Relación Pedagógica",
             "definicion": "Interacción, trato y disposición del docente hacia los estudiantes.",
             "criterios_inclusion": "Respeto, cercanía, disponibilidad para consultas, motivación, clima de aula.",
             "criterios_exclusion": "Capacidades técnicas o metodológicas del docente."},
        ],
    },
    "satisfaccion_estudiantil": {
        "nombre": "Satisfacción Estudiantil",
        "industria": "Educación Superior",
        "palabras_clave": ["estudiante", "alumno", "universidad", "campus", "biblioteca", "casino", "beca", "carrera", "matricula", "malla", "bienestar"],
        "descripcion": "Dimensiones habituales de encuestas de satisfacción: servicios, infraestructura, gestión académica y experiencia formativa.",
        "marco_teorico": (
            "Modelo de satisfacción estudiantil con cuatro dimensiones: experiencia formativa, "
            "servicios y apoyo estudiantil, infraestructura y recursos, y gestión académico-administrativa."
        ),
        "categorias_default": [
            {"nombre": "Experiencia Formativa",
             "definicion": "Percepción sobre la calidad de la formación recibida y su pertinencia.",
             "criterios_inclusion": "Calidad de los ramos, pertinencia del plan de estudios, preparación para el mundo laboral.",
             "criterios_exclusion": "Trámites administrativos o infraestructura."},
            {"nombre": "Servicios y Apoyo Estudiantil",
             "definicion": "Servicios de bienestar, salud, apoyo académico y financiero.",
             "criterios_inclusion": "Becas, salud mental, tutorías, bienestar, actividades extracurriculares.",
             "criterios_exclusion": "Salas, laboratorios o equipamiento (Infraestructura)."},
            {"nombre": "Infraestructura y Recursos",
             "definicion": "Espacios físicos, equipamiento, biblioteca y recursos tecnológicos.",
             "criterios_inclusion": "Salas, laboratorios, biblioteca, wifi, plataformas virtuales, campus.",
             "criterios_exclusion": "Calidad docente o de los servicios de apoyo."},
            {"nombre": "Gestión Académico-Administrativa",
             "definicion": "Procesos administrativos y de gestión académica.",
             "criterios_inclusion": "Toma de ramos, horarios, trámites, comunicación institucional, respuesta a solicitudes.",
             "criterios_exclusion": "Contenido o calidad de la enseñanza."},
        ],
    },
    "acreditacion_institucional": {
        "nombre": "Acreditación Institucional (CNA)",
        "industria": "Educación Superior",
        "palabras_clave": ["acreditacion", "institucional", "cna", "vinculacion", "aseguramiento", "autoevaluacion", "egresado", "investigacion"],
        "descripcion": "Dimensiones de la acreditación institucional CNA (Ley 21.091): docencia, gestión, aseguramiento interno de la calidad y vinculación con el medio.",
        "marco_teorico": (
            "Dimensiones de acreditación institucional CNA: docencia y resultados del proceso formativo, "
            "gestión estratégica y recursos institucionales, aseguramiento interno de la calidad, "
            "y vinculación con el medio."
        ),
        "categorias_default": [
            {"nombre": "Docencia y Resultados Formativos",
             "definicion": "Calidad del proceso formativo y sus resultados (progresión, titulación, empleabilidad).",
             "criterios_inclusion": "Enseñanza, acompañamiento, progresión académica, resultados de aprendizaje.",
             "criterios_exclusion": "Gestión de recursos o procesos administrativos."},
            {"nombre": "Gestión Estratégica y Recursos",
             "definicion": "Gobernanza, planificación y gestión de recursos institucionales.",
             "criterios_inclusion": "Planificación estratégica, gestión de recursos, sostenibilidad, gobernanza.",
             "criterios_exclusion": "Mecanismos de calidad (dimensión propia)."},
            {"nombre": "Aseguramiento Interno de la Calidad",
             "definicion": "Mecanismos sistemáticos de autorregulación y mejora continua.",
             "criterios_inclusion": "Autoevaluación, seguimiento de planes de mejora, sistemas de información para la calidad.",
             "criterios_exclusion": "Resultados formativos en sí mismos."},
            {"nombre": "Vinculación con el Medio",
             "definicion": "Relación bidireccional con el entorno social, productivo y cultural.",
             "criterios_inclusion": "Prácticas, convenios, extensión, impacto en el territorio, empleadores.",
             "criterios_exclusion": "Actividades puramente internas."},
        ],
    },

    # ================= ESTUDIOS DE MERCADO =================

    "satisfaccion_clientes_nps": {
        "nombre": "Satisfacción de Clientes (verbatims NPS)",
        "industria": "Estudios de Mercado",
        "palabras_clave": ["cliente", "recomend", "nps", "promotor", "detractor", "csat", "satisfaccion", "fidelidad"],
        "descripcion": "Para analizar los comentarios abiertos de encuestas NPS/CSAT: qué explica que un cliente sea promotor, pasivo o detractor.",
        "marco_teorico": (
            "Modelo de drivers de satisfacción y lealtad de clientes: calidad del producto o servicio, "
            "atención y servicio al cliente, precio y percepción de valor, y experiencia de canales "
            "(tienda, web, app, call center). Los verbatims NPS se codifican contra estos drivers para "
            "explicar el puntaje, no solo describirlo."
        ),
        "categorias_default": [
            {"nombre": "Calidad del Producto/Servicio",
             "definicion": "Desempeño del producto o servicio principal: si cumple lo que promete.",
             "criterios_inclusion": "Menciones a funcionamiento, durabilidad, calidad percibida, fallas o defectos del producto/servicio contratado, cumplimiento de lo ofrecido.",
             "criterios_exclusion": "El trato recibido de personas (Atención al Cliente), el precio pagado (Precio y Valor) o problemas para comprar/contratar (Experiencia de Canales)."},
            {"nombre": "Atención y Servicio al Cliente",
             "definicion": "Interacción con personas de la organización: trato, resolución y tiempos de respuesta.",
             "criterios_inclusion": "Amabilidad o mal trato del personal, rapidez o lentitud en resolver problemas, reclamos gestionados, postventa, soporte técnico humano.",
             "criterios_exclusion": "Fallas del producto en sí (Calidad) o dificultades con plataformas de autoatención sin intervención humana (Experiencia de Canales)."},
            {"nombre": "Precio y Percepción de Valor",
             "definicion": "Relación entre lo pagado y lo recibido: caro, barato, justo, conveniente.",
             "criterios_inclusion": "Menciones a precio, alzas, cobros, promociones, comparaciones de valor con la competencia, \"vale/no vale lo que cuesta\".",
             "criterios_exclusion": "Errores de facturación tratados como problema de servicio (Atención al Cliente) y calidad sin referencia al precio (Calidad)."},
            {"nombre": "Experiencia de Canales",
             "definicion": "Facilidad de uso de los canales de compra y contacto: tienda, sitio web, app, teléfono.",
             "criterios_inclusion": "Usabilidad de web/app, filas y tiempos en tienda, disponibilidad de stock, proceso de compra o contratación, entrega/despacho.",
             "criterios_exclusion": "El desempeño del producto ya adquirido (Calidad) o el trato del personal (Atención al Cliente)."},
            {"nombre": "Confianza y Reputación",
             "definicion": "Percepción de honestidad, transparencia y respaldo de la marca.",
             "criterios_inclusion": "Menciones a letra chica, engaño, transparencia, seguridad de datos, respaldo de la empresa, recomendaría/no recomendaría por principios.",
             "criterios_exclusion": "Insatisfacciones puntuales con producto, precio o servicio que no cuestionan la confianza en la marca."},
        ],
    },
    "percepcion_marca": {
        "nombre": "Percepción de Marca",
        "industria": "Estudios de Mercado",
        "palabras_clave": ["marca", "imagen", "posicionamiento", "competidor", "competencia", "publicidad", "asocia", "campana", "reputacion", "notoriedad"],
        "descripcion": "Para estudios de imagen y posicionamiento: asociaciones espontáneas, atributos funcionales y emocionales, y comparación con competidores.",
        "marco_teorico": (
            "Modelo de imagen de marca en tres capas: asociaciones funcionales (qué hace la marca y qué tan "
            "bien), asociaciones emocionales y simbólicas (qué siente y proyecta el consumidor), y "
            "posicionamiento relativo (cómo se compara con las alternativas). Se agrega la dimensión de "
            "comunicación y publicidad como fuente de esas asociaciones."
        ),
        "categorias_default": [
            {"nombre": "Atributos Funcionales",
             "definicion": "Asociaciones sobre el desempeño concreto de la marca: qué hace y qué tan bien lo hace.",
             "criterios_inclusion": "Calidad, variedad, cobertura, innovación, conveniencia, atributos verificables del producto o servicio.",
             "criterios_exclusion": "Sentimientos o valores proyectados (Atributos Emocionales) y comparaciones explícitas con otras marcas (Posicionamiento)."},
            {"nombre": "Atributos Emocionales y Simbólicos",
             "definicion": "Lo que la marca hace sentir y lo que proyecta socialmente al usarla.",
             "criterios_inclusion": "Cercanía, confianza, orgullo, nostalgia, estatus, identidad, \"marca para gente como yo\", personalidad de marca.",
             "criterios_exclusion": "Juicios sobre desempeño concreto (Atributos Funcionales)."},
            {"nombre": "Posicionamiento frente a Competidores",
             "definicion": "Comparaciones explícitas o implícitas con otras marcas de la categoría.",
             "criterios_inclusion": "\"Mejor/peor que X\", razones de preferencia o cambio de marca, ventajas y desventajas relativas.",
             "criterios_exclusion": "Evaluaciones absolutas de la marca sin punto de comparación."},
            {"nombre": "Comunicación y Publicidad",
             "definicion": "Percepción de campañas, mensajes, redes sociales y presencia pública de la marca.",
             "criterios_inclusion": "Recordación de campañas, tono de la comunicación, coherencia entre lo que promete y lo que entrega, presencia en medios y redes.",
             "criterios_exclusion": "Experiencias directas de compra o uso sin referencia a la comunicación."},
        ],
    },
    "investigacion_producto": {
        "nombre": "Investigación de Producto/Concepto",
        "industria": "Estudios de Mercado",
        "palabras_clave": ["concepto", "prototipo", "lanzamiento", "novedoso", "intencion", "pagar", "adopcion", "funcionalidad", "usaria"],
        "descripcion": "Para tests de concepto y feedback de producto: comprensión, relevancia, intención y barreras de adopción.",
        "marco_teorico": (
            "Marco de evaluación de conceptos y productos: comprensión del concepto (¿se entiende?), "
            "relevancia y necesidad (¿resuelve un problema real?), intención y disposición a pagar "
            "(¿lo compraría?), y barreras y objeciones (¿qué frena la adopción?). Incluye sugerencias "
            "de mejora como categoría accionable."
        ),
        "categorias_default": [
            {"nombre": "Comprensión del Concepto",
             "definicion": "Si el encuestado entiende qué es el producto y para qué sirve.",
             "criterios_inclusion": "Reformulaciones correctas o incorrectas del concepto, dudas sobre qué es o cómo funciona, confusiones con otros productos.",
             "criterios_exclusion": "Juicios de valor sobre si le gusta o lo compraría (otras categorías): aquí solo importa si lo entiende."},
            {"nombre": "Relevancia y Necesidad",
             "definicion": "Si el producto conecta con un problema o deseo real del encuestado.",
             "criterios_inclusion": "\"Me serviría para…\", identificación con la situación de uso, frecuencia del problema que resuelve, \"no lo necesito\".",
             "criterios_exclusion": "Objeciones de precio o desconfianza (Barreras) y juicios sobre claridad del concepto (Comprensión)."},
            {"nombre": "Intención y Disposición a Pagar",
             "definicion": "Señales de compra: cuándo, cuánto pagaría y en qué condiciones.",
             "criterios_inclusion": "\"Lo compraría si…\", rangos de precio aceptables, comparación con lo que paga hoy, condiciones para probarlo.",
             "criterios_exclusion": "Interés genérico sin señal de compra (Relevancia)."},
            {"nombre": "Barreras y Objeciones",
             "definicion": "Frenos concretos a la adopción: desconfianza, precio, hábito, complejidad.",
             "criterios_inclusion": "\"Es muy caro\", \"no confío\", \"ya uso otra cosa\", \"parece complicado\", miedos y riesgos percibidos.",
             "criterios_exclusion": "Desinterés por irrelevancia (\"no lo necesito\" → Relevancia y Necesidad)."},
            {"nombre": "Sugerencias de Mejora",
             "definicion": "Propuestas concretas del encuestado para mejorar el producto o concepto.",
             "criterios_inclusion": "\"Debería tener…\", \"me gustaría que…\", cambios a atributos, formatos, canales o precios propuestos por el encuestado.",
             "criterios_exclusion": "Críticas sin propuesta (van en la categoría del problema correspondiente)."},
        ],
    },

    # ================= ORGANIZACIONES Y B2B =================

    "clima_organizacional": {
        "nombre": "Clima y Cultura Organizacional",
        "industria": "Organizaciones y B2B",
        "palabras_clave": ["clima", "jefatura", "jefe", "liderazgo", "equipo", "companero", "organizacion", "reconocimiento", "remuneracion", "cultura"],
        "descripcion": "Para encuestas de clima: liderazgo, colaboración, desarrollo, reconocimiento y condiciones de trabajo.",
        "marco_teorico": (
            "Modelo de clima organizacional en cinco dimensiones: liderazgo y confianza en jefaturas, "
            "colaboración y relaciones entre equipos, desarrollo y crecimiento profesional, reconocimiento "
            "y compensación, y condiciones y carga de trabajo. La cultura emerge de patrones transversales "
            "entre estas dimensiones."
        ),
        "categorias_default": [
            {"nombre": "Liderazgo y Jefaturas",
             "definicion": "Percepción de los líderes directos y la plana directiva: confianza, comunicación y coherencia.",
             "criterios_inclusion": "Trato de la jefatura, retroalimentación recibida, claridad de las directrices, coherencia entre el discurso y la práctica, accesibilidad de los líderes.",
             "criterios_exclusion": "Relaciones entre pares (Colaboración) y decisiones de compensación (Reconocimiento y Compensación)."},
            {"nombre": "Colaboración y Relaciones",
             "definicion": "Calidad de las relaciones y la cooperación entre personas y equipos.",
             "criterios_inclusion": "Trabajo en equipo, compañerismo, conflictos entre áreas, silos, comunicación horizontal, ambiente entre colegas.",
             "criterios_exclusion": "Relación con jefaturas (Liderazgo) y sobrecarga por mala coordinación tratada como carga (Condiciones y Carga)."},
            {"nombre": "Desarrollo y Crecimiento",
             "definicion": "Oportunidades de aprendizaje, movilidad interna y proyección de carrera.",
             "criterios_inclusion": "Capacitación, ascensos, planes de carrera, aprendizaje en el cargo, estancamiento profesional.",
             "criterios_exclusion": "Sueldo y beneficios (Reconocimiento y Compensación)."},
            {"nombre": "Reconocimiento y Compensación",
             "definicion": "Percepción de justicia en sueldos, beneficios y reconocimiento del aporte.",
             "criterios_inclusion": "Sueldo, bonos, beneficios, equidad interna, sentirse valorado o invisibilizado, reconocimiento no monetario.",
             "criterios_exclusion": "Oportunidades de carrera sin referencia a compensación (Desarrollo)."},
            {"nombre": "Condiciones y Carga de Trabajo",
             "definicion": "Carga laboral, equilibrio vida-trabajo, herramientas e infraestructura para trabajar.",
             "criterios_inclusion": "Horas extra, estrés, dotación insuficiente, flexibilidad, teletrabajo, herramientas y sistemas, espacios físicos.",
             "criterios_exclusion": "Malestar cuya causa es el trato de personas (Liderazgo o Colaboración)."},
        ],
    },
    "feedback_empleados": {
        "nombre": "Feedback de Empleados (pulso / salida)",
        "industria": "Organizaciones y B2B",
        "palabras_clave": ["renuncia", "permanencia", "pulso", "empleado", "trabajador", "desvincul", "rotacion", "onboarding"],
        "descripcion": "Para encuestas de pulso y entrevistas de salida: motivos de permanencia y renuncia, momentos críticos y propuestas.",
        "marco_teorico": (
            "Marco de experiencia del empleado (employee journey): motivos de permanencia (qué retiene), "
            "motivos de salida o malestar (qué expulsa), momentos críticos del ciclo laboral (ingreso, "
            "cambios de rol, evaluaciones), y propuestas de mejora. Diseñado para pulsos frecuentes y "
            "entrevistas de salida donde importa distinguir el detonante del contexto."
        ),
        "categorias_default": [
            {"nombre": "Motivos de Permanencia",
             "definicion": "Lo que retiene a la persona en la organización: qué valora y no quiere perder.",
             "criterios_inclusion": "\"Me quedo por…\", equipo, propósito, estabilidad, beneficios valorados, orgullo de pertenencia.",
             "criterios_exclusion": "Quejas o malestares (Motivos de Salida) y sugerencias a futuro (Propuestas)."},
            {"nombre": "Motivos de Salida o Malestar",
             "definicion": "Detonantes y causas de renuncia, desmotivación o búsqueda activa de otro empleo.",
             "criterios_inclusion": "Razones de renuncia declaradas, ofertas externas, burnout, conflictos, promesas incumplidas, techo de crecimiento.",
             "criterios_exclusion": "Incomodidades menores sin señal de salida ni desmotivación sostenida."},
            {"nombre": "Momentos Críticos del Ciclo",
             "definicion": "Experiencias en hitos específicos: onboarding, cambio de rol, evaluación, reestructuración.",
             "criterios_inclusion": "Relatos anclados a un hito: \"cuando entré…\", \"tras la evaluación…\", \"con la reestructuración…\", transiciones y cambios organizacionales.",
             "criterios_exclusion": "Percepciones generales sin referencia a un momento o hito identificable."},
            {"nombre": "Propuestas y Sugerencias",
             "definicion": "Ideas concretas del empleado para mejorar la experiencia laboral.",
             "criterios_inclusion": "\"Deberían…\", \"ayudaría que…\", propuestas accionables sobre procesos, beneficios, comunicación o liderazgo.",
             "criterios_exclusion": "Críticas sin propuesta (van en la categoría del malestar correspondiente)."},
        ],
    },
    "voz_cliente_b2b": {
        "nombre": "Voz del Cliente B2B",
        "industria": "Organizaciones y B2B",
        "palabras_clave": ["b2b", "proveedor", "contrato", "soporte", "partnership", "comercial", "facturacion", "ejecutivo"],
        "descripcion": "Para feedback de clientes empresa: relación comercial, calidad de la entrega, soporte y valor percibido del partnership.",
        "marco_teorico": (
            "Marco de relación cliente-proveedor B2B: gestión comercial y de cuenta (la relación), calidad "
            "de la entrega o implementación (el trabajo), soporte y respuesta ante problemas (la reacción), "
            "y valor estratégico del partnership (el resultado de negocio). En B2B el encuestado suele hablar "
            "por su organización, no solo por sí mismo."
        ),
        "categorias_default": [
            {"nombre": "Gestión Comercial y de Cuenta",
             "definicion": "Relación con ejecutivos y gestión contractual: cercanía, proactividad y flexibilidad.",
             "criterios_inclusion": "Trato del ejecutivo de cuenta, frecuencia de contacto, negociaciones, contratos, cotizaciones, proactividad comercial.",
             "criterios_exclusion": "Ejecución técnica del servicio (Calidad de la Entrega) y resolución de incidentes (Soporte)."},
            {"nombre": "Calidad de la Entrega",
             "definicion": "Ejecución del producto o servicio contratado: plazos, especificaciones y estándares.",
             "criterios_inclusion": "Cumplimiento de plazos y alcances, calidad técnica del trabajo, errores de implementación, consistencia entre proyectos.",
             "criterios_exclusion": "Problemas resueltos (o no) después de la entrega (Soporte) y percepciones de precio (Valor del Partnership)."},
            {"nombre": "Soporte y Respuesta",
             "definicion": "Reacción del proveedor ante problemas, dudas e incidentes post-entrega.",
             "criterios_inclusion": "Tiempos de respuesta, escalamiento, mesa de ayuda, seguimiento de tickets, comunicación durante incidentes.",
             "criterios_exclusion": "Defectos de la entrega original (Calidad de la Entrega)."},
            {"nombre": "Valor del Partnership",
             "definicion": "Aporte del proveedor al negocio del cliente: retorno, innovación y proyección conjunta.",
             "criterios_inclusion": "Relación precio-valor, impacto en resultados del cliente, aporte de ideas e innovación, intención de renovar o ampliar el contrato.",
             "criterios_exclusion": "Satisfacciones operativas puntuales sin referencia al valor de negocio."},
        ],
    },

    # ================= SECTOR PÚBLICO =================

    "consultas_ciudadanas": {
        "nombre": "Consultas Ciudadanas",
        "industria": "Sector Público",
        "palabras_clave": ["ciudadan", "participacion", "consulta", "autoridad", "gobierno", "demanda", "legitimidad", "politica", "representante"],
        "descripcion": "Para procesos participativos: demandas y prioridades, evaluación de la gestión, propuestas y confianza institucional.",
        "marco_teorico": (
            "Marco de análisis de participación ciudadana: demandas y necesidades priorizadas por la "
            "comunidad, evaluación de la gestión actual, propuestas ciudadanas concretas, y confianza y "
            "legitimidad institucional. Diseñado para consultas, cabildos, presupuestos participativos y "
            "procesos de consulta normativa."
        ),
        "categorias_default": [
            {"nombre": "Demandas y Necesidades",
             "definicion": "Problemas y carencias que la ciudadanía pide resolver, con su priorización implícita.",
             "criterios_inclusion": "Necesidades de seguridad, salud, transporte, áreas verdes, vivienda u otras; urgencias declaradas; \"lo que más falta es…\".",
             "criterios_exclusion": "Juicios sobre lo que la autoridad ya hizo (Evaluación de la Gestión) y soluciones detalladas (Propuestas Ciudadanas)."},
            {"nombre": "Evaluación de la Gestión",
             "definicion": "Juicios sobre el desempeño de la autoridad o el servicio: qué se ha hecho bien o mal.",
             "criterios_inclusion": "Aprobación o crítica de obras, programas y decisiones; comparaciones con gestiones anteriores; cumplimiento de compromisos.",
             "criterios_exclusion": "Desconfianza generalizada hacia las instituciones sin referencia a una gestión concreta (Confianza Institucional)."},
            {"nombre": "Propuestas Ciudadanas",
             "definicion": "Soluciones e ideas concretas aportadas por la comunidad.",
             "criterios_inclusion": "\"Propongo que…\", proyectos específicos, cambios normativos sugeridos, ideas con lugar/mecanismo identificable.",
             "criterios_exclusion": "Peticiones genéricas sin contenido de solución (Demandas y Necesidades)."},
            {"nombre": "Confianza y Legitimidad",
             "definicion": "Percepción de transparencia, probidad y disposición a participar en el proceso.",
             "criterios_inclusion": "Menciones a corrupción, transparencia, \"no nos escuchan\", escepticismo sobre el uso de la consulta, valoración del espacio participativo.",
             "criterios_exclusion": "Críticas a resultados concretos de gestión (Evaluación de la Gestión)."},
        ],
    },
    "servicios_publicos": {
        "nombre": "Evaluación de Servicios Públicos",
        "industria": "Sector Público",
        "palabras_clave": ["tramite", "ventanilla", "funcionario", "publico", "beneficio", "requisito", "certificado", "reparticion", "usuario"],
        "descripcion": "Para encuestas de usuarios de servicios estatales: acceso, calidad de atención, tiempos y trámites, e información.",
        "marco_teorico": (
            "Modelo de experiencia del usuario de servicios públicos: acceso y cobertura (poder llegar al "
            "servicio), calidad de la atención (el trato recibido), eficiencia de trámites y tiempos "
            "(el costo en tiempo y gestiones), y claridad de la información (entender qué hacer). "
            "Alineado con los estándares de satisfacción usuaria del Estado chileno."
        ),
        "categorias_default": [
            {"nombre": "Acceso y Cobertura",
             "definicion": "Posibilidad real de llegar al servicio: horarios, distancia, canales disponibles, cupos.",
             "criterios_inclusion": "Distancia y traslados, horarios de atención, disponibilidad de horas/cupos, acceso digital vs presencial, brechas territoriales.",
             "criterios_exclusion": "El trato una vez atendido (Calidad de la Atención) y la demora del trámite mismo (Tiempos y Trámites)."},
            {"nombre": "Calidad de la Atención",
             "definicion": "Trato y competencia del personal que atiende al usuario.",
             "criterios_inclusion": "Amabilidad o maltrato, disposición a ayudar, competencia del funcionario, dignidad del trato, discriminación.",
             "criterios_exclusion": "Demoras de proceso sin referencia al trato (Tiempos y Trámites)."},
            {"nombre": "Tiempos y Trámites",
             "definicion": "Eficiencia del proceso: esperas, pasos, requisitos y burocracia.",
             "criterios_inclusion": "Filas y tiempos de espera, cantidad de pasos y papeles, trámites repetidos, plazos de resolución, \"me mandan de una oficina a otra\".",
             "criterios_exclusion": "No poder acceder al servicio en absoluto (Acceso y Cobertura)."},
            {"nombre": "Información y Claridad",
             "definicion": "Si el usuario entiende qué debe hacer, qué necesita y en qué estado va su solicitud.",
             "criterios_inclusion": "Instrucciones confusas, requisitos no informados, seguimiento del estado del trámite, lenguaje técnico incomprensible, señalética.",
             "criterios_exclusion": "Quejas de demora o trato que no involucran falta de información."},
        ],
    },

    # ================= SALUD =================

    "experiencia_pacientes": {
        "nombre": "Experiencia de Pacientes",
        "industria": "Salud",
        "palabras_clave": ["paciente", "hospital", "consultorio", "cesfam", "medico", "doctor", "enfermer", "clinic", "salud", "urgencia", "tratamiento", "diagnostico"],
        "descripcion": "Para encuestas de pacientes y familiares: trato del equipo clínico, información recibida, acceso y tiempos, e infraestructura.",
        "marco_teorico": (
            "Modelo de experiencia del paciente (patient experience): trato y humanización del equipo de "
            "salud, comunicación e información clínica (entender el diagnóstico y el tratamiento), acceso "
            "y oportunidad de la atención (conseguir hora y ser atendido a tiempo), y entorno e "
            "infraestructura del recinto. La experiencia reportada complementa —no reemplaza— los "
            "indicadores clínicos de calidad."
        ),
        "categorias_default": [
            {"nombre": "Trato y Humanización",
             "definicion": "Calidad humana del contacto con el equipo de salud: respeto, empatía y dignidad.",
             "criterios_inclusion": "Amabilidad o frialdad del personal clínico y administrativo, respeto por el pudor y el dolor, contención emocional, trato a la familia.",
             "criterios_exclusion": "Explicaciones médicas confusas (Comunicación e Información) y demoras (Acceso y Oportunidad)."},
            {"nombre": "Comunicación e Información Clínica",
             "definicion": "Claridad de la información sobre diagnóstico, tratamiento, medicamentos y pasos a seguir.",
             "criterios_inclusion": "Explicaciones del médico entendidas o no, consentimiento informado, indicaciones al alta, información contradictoria entre profesionales.",
             "criterios_exclusion": "El tono o calidez del trato sin contenido informativo (Trato y Humanización)."},
            {"nombre": "Acceso y Oportunidad",
             "definicion": "Conseguir atención cuando se necesita: horas, esperas, derivaciones y urgencias.",
             "criterios_inclusion": "Disponibilidad de horas, listas de espera, tiempos en urgencia, demoras de exámenes y resultados, derivaciones que no avanzan.",
             "criterios_exclusion": "Esperas dentro de una consulta ya obtenida por desorganización del recinto (Entorno e Infraestructura) — usar juicio según el énfasis del relato."},
            {"nombre": "Entorno e Infraestructura",
             "definicion": "Condiciones físicas del recinto: limpieza, comodidad, equipamiento y organización.",
             "criterios_inclusion": "Higiene, estado de salas y baños, camas y equipamiento, alimentación hospitalaria, señalética, ruido y privacidad.",
             "criterios_exclusion": "El desempeño de las personas (Trato) o del sistema de agendamiento (Acceso)."},
        ],
    },

    # ================= RETAIL =================

    "retail_experiencia_tienda": {
        "nombre": "Experiencia en Tienda",
        "industria": "Retail",
        "palabras_clave": ["tienda", "caja", "vendedor", "probador", "stock", "promocion", "devolucion", "boleta", "cajero", "pasillo"],
        "descripcion": "Para encuestas a clientes que compraron en tienda física: atención, disponibilidad de productos, caja, precios y cambios.",
        "marco_teorico": (
            "Modelo de experiencia de compra en tienda: cómo te atienden (el trato), si encuentras lo que "
            "buscas (productos y orden de la tienda), cuánto te demoras en pagar (la caja), cuánto cuesta lo "
            "que compras (precio y promociones) y qué pasa si algo sale mal (cambios y devoluciones). "
            "Cada comentario se asigna a la parte de la visita que más pesa en lo que cuenta el cliente."
        ),
        "categorias_default": [
            {"nombre": "Atención del Personal",
             "definicion": "Trato y disposición de vendedores, personal de piso y servicio al cliente dentro de la tienda.",
             "criterios_inclusion": "Amabilidad o mala cara, ayuda para encontrar un producto, conocimiento del vendedor, insistencia o abandono del cliente, tiempo para ser atendido en el mesón.",
             "criterios_exclusion": "Demoras en la fila de pago (Caja y Tiempos de Espera) y atención en reclamos por cambios o devoluciones (Cambios y Devoluciones)."},
            {"nombre": "Productos y Disponibilidad",
             "definicion": "Si la tienda tiene lo que el cliente busca, en la talla, color o cantidad que necesita, y si está ordenado y a la vista.",
             "criterios_inclusion": "Quiebres de stock, falta de tallas, variedad de productos, orden de las góndolas, productos mal ubicados, señalética para encontrar secciones.",
             "criterios_exclusion": "Calidad o fallas del producto ya comprado (Cambios y Devoluciones) y el precio de lo que se encuentra (Precio y Promociones)."},
            {"nombre": "Caja y Tiempos de Espera",
             "definicion": "Rapidez y comodidad al pagar: filas, cajas abiertas y medios de pago.",
             "criterios_inclusion": "Filas largas, pocas cajas habilitadas, autoservicio de pago, problemas con la tarjeta o el sistema de pago, demora en el empaque.",
             "criterios_exclusion": "Espera para ser atendido por un vendedor (Atención del Personal) y cobros mal aplicados por precios o descuentos (Precio y Promociones)."},
            {"nombre": "Precio y Promociones",
             "definicion": "Percepción de precios, ofertas, descuentos y convenios, y si lo cobrado coincide con lo anunciado.",
             "criterios_inclusion": "Precios caros o convenientes, ofertas que no se cumplen, diferencias entre el precio de góndola y el de caja, descuentos con tarjeta, programas de puntos.",
             "criterios_exclusion": "Falta de stock de un producto en oferta (Productos y Disponibilidad) y demoras en la fila (Caja y Tiempos de Espera)."},
            {"nombre": "Cambios y Devoluciones",
             "definicion": "Experiencia al cambiar o devolver un producto, y respuesta de la tienda ante un problema con lo comprado.",
             "criterios_inclusion": "Facilidad o trabas para cambiar, plazos, exigencia de boleta, reembolsos, garantía, productos defectuosos que el cliente quiso devolver.",
             "criterios_exclusion": "Variedad o falta de stock al momento de comprar (Productos y Disponibilidad) y trato general del personal sin relación con un cambio (Atención del Personal)."},
        ],
    },
    "retail_post_compra_nps": {
        "nombre": "Post-compra y NPS",
        "industria": "Retail",
        "palabras_clave": ["compra", "recomend", "nps", "postcompra", "volveria", "recompra", "producto"],
        "descripcion": "Para los comentarios abiertos de la encuesta NPS que se envía después de una compra, en tienda o en línea: qué hace que un cliente recomiende o no la marca.",
        "marco_teorico": (
            "Modelo de lealtad del cliente después de comprar: qué tal es lo que compró (producto), cómo fue "
            "el proceso de compra, cómo lo trató la empresa si necesitó ayuda (servicio), si sintió que valió "
            "lo que pagó (precio y valor) y si confía en la marca. Los comentarios se codifican contra estos "
            "motivos para explicar el puntaje NPS, no solo describirlo."
        ),
        "categorias_default": [
            {"nombre": "Producto Comprado",
             "definicion": "Cómo es el producto que el cliente compró: calidad, variedad y si cumple lo que esperaba.",
             "criterios_inclusion": "Calidad, durabilidad, talla y calce, que el producto sea igual a la foto o descripción, fallas o defectos, variedad del surtido.",
             "criterios_exclusion": "Cómo llegó o cuánto demoró en llegar (Experiencia de Compra) y el trato recibido al reclamar (Servicio al Cliente)."},
            {"nombre": "Experiencia de Compra",
             "definicion": "Qué tan fácil o difícil fue comprar, en tienda o por la web o app.",
             "criterios_inclusion": "Facilidad para encontrar y pagar, fallas del sitio o la app, filas, retiro en tienda, disponibilidad al momento de comprar.",
             "criterios_exclusion": "Cumplimiento del plazo de entrega a domicilio (el detalle del despacho va en la plantilla Despacho y E-commerce) y el producto ya recibido (Producto Comprado)."},
            {"nombre": "Servicio al Cliente",
             "definicion": "Trato y capacidad de resolver problemas cuando el cliente necesitó ayuda de una persona de la empresa.",
             "criterios_inclusion": "Amabilidad, rapidez de respuesta, reclamos resueltos o ignorados, cambios y devoluciones, atención por teléfono, chat o correo.",
             "criterios_exclusion": "Falla del producto sin contacto con la empresa (Producto Comprado) y problemas de la web o la app sin intervención de una persona (Experiencia de Compra)."},
            {"nombre": "Precio y Valor",
             "definicion": "Si el cliente siente que lo que pagó fue justo o conveniente por lo que recibió.",
             "criterios_inclusion": "Precio caro o barato, ofertas y descuentos, comparación con otras tiendas, \"vale lo que cuesta\", cobros inesperados o costos de envío.",
             "criterios_exclusion": "Calidad del producto sin mencionar el precio (Producto Comprado) y atención en la devolución del dinero (Servicio al Cliente)."},
            {"nombre": "Confianza y Recomendación",
             "definicion": "Confianza en la marca y razones del cliente para recomendarla o no.",
             "criterios_inclusion": "\"Volvería a comprar\", \"no la recomiendo\", honestidad de la publicidad, cumplimiento de lo prometido, seguridad de los datos y del pago, reputación de la marca.",
             "criterios_exclusion": "Molestias puntuales con el producto, el precio o la atención que no cuestionan la confianza en la marca (Producto Comprado, Precio y Valor o Servicio al Cliente, según el tema)."},
        ],
    },
    "retail_despacho_ecommerce": {
        "nombre": "Despacho y E-commerce",
        "industria": "Retail",
        "palabras_clave": ["despacho", "pedido", "envio", "courier", "seguimiento", "ecommerce", "domicilio", "tracking", "repartidor", "retiro", "paquete"],
        "descripcion": "Para encuestas a clientes que compraron en línea: cumplimiento del plazo de despacho, estado del producto al llegar, seguimiento del pedido y uso del sitio.",
        "marco_teorico": (
            "Modelo de la compra en línea de principio a fin: usar el sitio o la app para elegir y pagar, "
            "esperar el pedido (plazo y seguimiento), recibirlo (entrega y estado del producto) y resolver "
            "problemas si algo falla (postventa). Cada etapa tiene su propio responsable dentro de la empresa, "
            "por eso se separan."
        ),
        "categorias_default": [
            {"nombre": "Sitio y Proceso de Compra",
             "definicion": "Facilidad de usar el sitio web o la app para buscar, elegir y pagar.",
             "criterios_inclusion": "Navegación, buscador, fotos y descripciones, fallas al pagar, carro de compras, medios de pago, claridad del costo de envío antes de pagar.",
             "criterios_exclusion": "Lo que ocurre después de pagar (Plazo de Despacho y Seguimiento) y la calidad del producto recibido (Estado y Contenido del Pedido)."},
            {"nombre": "Plazo de Despacho y Seguimiento",
             "definicion": "Cumplimiento de la fecha prometida y capacidad de saber dónde va el pedido.",
             "criterios_inclusion": "Atrasos, entrega antes o después de lo prometido, número de seguimiento que no se actualiza, falta de avisos, reprogramaciones, pedido perdido.",
             "criterios_exclusion": "Trato del repartidor al entregar (Entrega y Retiro) y problemas del pedido ya recibido (Estado y Contenido del Pedido)."},
            {"nombre": "Entrega y Retiro",
             "definicion": "Cómo fue el momento de recibir el pedido, a domicilio o retirándolo en tienda o punto de retiro.",
             "criterios_inclusion": "Trato del repartidor, entrega fuera del horario acordado, nadie en casa, visitas fallidas, retiro en tienda, espera en el punto de retiro, entrega en el lugar equivocado.",
             "criterios_exclusion": "Atraso general del despacho antes de la entrega (Plazo de Despacho y Seguimiento) y daños del producto (Estado y Contenido del Pedido)."},
            {"nombre": "Estado y Contenido del Pedido",
             "definicion": "Cómo llegó el pedido: si estaba completo, bien embalado y era lo que se compró.",
             "criterios_inclusion": "Productos dañados o rotos, embalaje deficiente, productos faltantes o equivocados, bultos incompletos, productos usados o con fallas al abrirlos.",
             "criterios_exclusion": "Demoras en llegar (Plazo de Despacho y Seguimiento) y la gestión del cambio o reembolso (Postventa y Devoluciones)."},
            {"nombre": "Postventa y Devoluciones",
             "definicion": "Respuesta de la empresa cuando el cliente reclama, cambia o devuelve algo de una compra en línea.",
             "criterios_inclusion": "Facilidad o trabas para devolver, retiro del producto a devolver, reembolsos, tiempos de respuesta del servicio al cliente, reclamos sin solución.",
             "criterios_exclusion": "El problema de origen, como un producto dañado o un atraso (Estado y Contenido del Pedido o Plazo de Despacho y Seguimiento); aquí solo importa cómo respondió la empresa."},
        ],
    },
    "retail_colaboradores_tienda": {
        "nombre": "Colaboradores de Tienda",
        "industria": "Retail",
        "palabras_clave": ["turno", "colaborador", "capacitacion", "tienda", "reponedor", "inventario", "comision", "uniforme", "bodega"],
        "descripcion": "Para encuestas internas al personal de tiendas: clima laboral, carga de trabajo, turnos, jefaturas, capacitación y condiciones del local.",
        "marco_teorico": (
            "Modelo de clima laboral en tiendas, adaptado a la realidad del retail: trabajo en turnos y con "
            "público. Mira cómo es la carga del día a día (dotación, turnos, metas de venta), la relación con "
            "la jefatura de tienda, el compañerismo, el aprendizaje y las oportunidades de crecer, y las "
            "condiciones físicas del local. Sirve para entender qué desgasta o motiva al personal que atiende "
            "al cliente."
        ),
        "categorias_default": [
            {"nombre": "Carga de Trabajo y Turnos",
             "definicion": "Cantidad de trabajo, horarios y turnos, y su efecto en el descanso y la vida personal.",
             "criterios_inclusion": "Falta de dotación, turnos rotativos, horas extra, pocos días libres, trabajo en fines de semana y festivos, presión por metas de venta, cansancio.",
             "criterios_exclusion": "Malestar por el trato de la jefatura (Liderazgo en Tienda) y sueldo o bonos (Remuneración y Reconocimiento)."},
            {"nombre": "Liderazgo en Tienda",
             "definicion": "Relación con el jefe de tienda, supervisores y la gerencia: trato, comunicación y justicia.",
             "criterios_inclusion": "Trato de la jefatura, favoritismos, claridad de las instrucciones, retroalimentación, escucha ante problemas, coherencia entre lo que se dice y lo que se hace.",
             "criterios_exclusion": "Relación entre compañeros de turno (Compañerismo y Ambiente) y la presión por metas como carga (Carga de Trabajo y Turnos)."},
            {"nombre": "Compañerismo y Ambiente",
             "definicion": "Relación entre colegas del mismo equipo y entre secciones o turnos de la tienda.",
             "criterios_inclusion": "Ayuda mutua, buen o mal ambiente, conflictos entre compañeros, traspaso entre turnos, trato entre secciones, discriminación o malos tratos entre pares.",
             "criterios_exclusion": "Relación con la jefatura (Liderazgo en Tienda) y problemas con clientes difíciles (Condiciones del Local y Seguridad)."},
            {"nombre": "Capacitación y Desarrollo",
             "definicion": "Preparación para el cargo y posibilidades de aprender y avanzar dentro de la empresa.",
             "criterios_inclusion": "Inducción al entrar, capacitaciones, cursos, ascensos, cambios a otros cargos o tiendas, acceso a información de productos y procesos.",
             "criterios_exclusion": "Sueldo, bonos y comisiones (Remuneración y Reconocimiento) y falta de dotación que impide capacitarse (Carga de Trabajo y Turnos)."},
            {"nombre": "Remuneración y Reconocimiento",
             "definicion": "Percepción de justicia en el sueldo, las comisiones, los beneficios y el reconocimiento del esfuerzo.",
             "criterios_inclusion": "Sueldo base, comisiones y bonos por venta, beneficios, descuentos de personal, equidad entre colegas, sentirse valorado o ignorado.",
             "criterios_exclusion": "Oportunidades de ascenso sin mención al pago (Capacitación y Desarrollo) y metas de venta como presión de trabajo (Carga de Trabajo y Turnos)."},
            {"nombre": "Condiciones del Local y Seguridad",
             "definicion": "Estado físico del lugar de trabajo, herramientas, seguridad y trato de clientes hacia el personal.",
             "criterios_inclusion": "Bodega, comedor y baños del personal, temperatura, mobiliario, sistemas de caja y de inventario, robos o asaltos, clientes agresivos, uniformes, prevención de accidentes.",
             "criterios_exclusion": "Cansancio por jornadas o dotación (Carga de Trabajo y Turnos) y conflictos con compañeros (Compañerismo y Ambiente)."},
        ],
    },

    # ================= MUNICIPAL =================

    "municipal_servicios": {
        "nombre": "Satisfacción con Servicios Municipales",
        "industria": "Municipal",
        "palabras_clave": ["municipal", "municipio", "vecino", "aseo", "ornato", "basura", "alumbrado", "comuna", "alcalde", "plaza"],
        "descripcion": "Para encuestas a vecinos sobre los servicios que entrega el municipio: atención y trámites, aseo y ornato, seguridad y áreas verdes.",
        "marco_teorico": (
            "Modelo de satisfacción vecinal con los servicios del municipio: la atención y los trámites en "
            "oficinas, el aseo y ornato de calles y espacios públicos, la seguridad del barrio, y las áreas "
            "verdes y la infraestructura que usa la comunidad. Cada comentario se asigna al servicio del que "
            "habla el vecino, para que cada dirección municipal sepa qué le toca mejorar."
        ),
        "categorias_default": [
            {"nombre": "Atención y Trámites",
             "definicion": "Experiencia del vecino al hacer trámites o consultas en las oficinas municipales, por teléfono o en línea.",
             "criterios_inclusion": "Trato de los funcionarios, filas y tiempos de espera, permisos, patentes, certificados, claridad de los requisitos, horarios de atención, trámites por internet.",
             "criterios_exclusion": "Reclamos por la mantención del barrio, como basura o luminarias (Aseo y Ornato), y por la seguridad (Seguridad Ciudadana)."},
            {"nombre": "Aseo y Ornato",
             "definicion": "Limpieza y mantención de calles, veredas, alumbrado y espacios públicos del barrio.",
             "criterios_inclusion": "Retiro de basura, microbasurales, barrido de calles, luminarias quemadas, veredas y calles en mal estado, ferias y comercio ambulante, escombros.",
             "criterios_exclusion": "Plazas, árboles y jardines (Áreas Verdes y Espacios Públicos) y delincuencia o falta de vigilancia aunque ocurra por mala iluminación (Seguridad Ciudadana)."},
            {"nombre": "Seguridad Ciudadana",
             "definicion": "Sensación de seguridad en el barrio y trabajo del municipio con las policías y la prevención.",
             "criterios_inclusion": "Robos, balaceras, consumo de alcohol y drogas en la vía pública, patrullajes, cámaras de vigilancia, alarmas comunitarias, seguridad de noche, ruidos molestos.",
             "criterios_exclusion": "Mantención de luminarias o calles sin mención a la seguridad (Aseo y Ornato) y trato del funcionario en una denuncia o trámite (Atención y Trámites)."},
            {"nombre": "Áreas Verdes y Espacios Públicos",
             "definicion": "Estado, cantidad y uso de plazas, parques, canchas, juegos infantiles y otros lugares de encuentro.",
             "criterios_inclusion": "Mantención de plazas y parques, riego, poda de árboles, canchas y multicanchas, juegos infantiles, ciclovías, accesibilidad, falta de espacios para la comunidad.",
             "criterios_exclusion": "Limpieza general de calles y basura (Aseo y Ornato) e inseguridad en una plaza (Seguridad Ciudadana)."},
            {"nombre": "Servicios y Programas Sociales",
             "definicion": "Programas del municipio para las personas: salud municipal, educación, cultura, deportes y apoyo social.",
             "criterios_inclusion": "Consultorios y Cesfam municipales, colegios municipales, talleres, actividades culturales y deportivas, beneficios para adultos mayores, ayudas sociales, programas para jóvenes y mujeres.",
             "criterios_exclusion": "Trato en una oficina por un trámite cualquiera (Atención y Trámites) y estado de canchas o plazas como infraestructura (Áreas Verdes y Espacios Públicos)."},
        ],
    },
    "municipal_pladeco": {
        "nombre": "Consulta PLADECO",
        "industria": "Municipal",
        "palabras_clave": ["pladeco", "comuna", "territorial", "emprendimiento", "empleo", "ambiente", "desarrollo", "vecino", "proyecto"],
        "descripcion": "Para la consulta a la comunidad del Plan de Desarrollo Comunal (PLADECO): en qué ámbitos quieren los vecinos que avance la comuna y con qué proyectos.",
        "marco_teorico": (
            "El PLADECO es el plan que define hacia dónde quiere avanzar una comuna en los próximos años. "
            "Esta plantilla ordena las respuestas de la comunidad por ámbito de desarrollo: social, "
            "territorial y medio ambiente, económico y empleo, e institucional. Aparte se recogen las "
            "propuestas de proyectos concretos, que se pueden cruzar con cada ámbito."
        ),
        "categorias_default": [
            {"nombre": "Desarrollo Social y Comunitario",
             "definicion": "Prioridades de las personas y la vida en comunidad: salud, educación, vivienda, cultura, deporte, adultos mayores, infancia y organizaciones sociales.",
             "criterios_inclusion": "Falta de atención de salud, calidad de la educación, acceso a vivienda, apoyo a adultos mayores y jóvenes, vida comunitaria, cultura y deporte, igualdad y inclusión.",
             "criterios_exclusion": "Obras, transporte o medio ambiente (Desarrollo Territorial y Medio Ambiente), empleo y comercio (Desarrollo Económico y Empleo) y proyectos con nombre y lugar (Propuestas de Proyectos)."},
            {"nombre": "Desarrollo Territorial y Medio Ambiente",
             "definicion": "Prioridades sobre cómo se ocupa y cuida el territorio: obras, conectividad, vivienda en el espacio urbano, seguridad del entorno y medio ambiente.",
             "criterios_inclusion": "Transporte y conectividad, calles y veredas, áreas verdes, agua, basura y reciclaje, contaminación, riesgo de inundaciones o incendios, crecimiento urbano, seguridad del entorno.",
             "criterios_exclusion": "Servicios a las personas, como salud o educación (Desarrollo Social y Comunitario) y peticiones de un proyecto puntual (Propuestas de Proyectos)."},
            {"nombre": "Desarrollo Económico y Empleo",
             "definicion": "Prioridades sobre trabajo, emprendimiento, comercio y turismo en la comuna.",
             "criterios_inclusion": "Falta de empleo, capacitación laboral, apoyo a emprendedores y pymes, ferias, comercio local, turismo, patentes, atracción de empresas.",
             "criterios_exclusion": "Educación y capacitación general sin fin laboral (Desarrollo Social y Comunitario) y obras de infraestructura (Desarrollo Territorial y Medio Ambiente)."},
            {"nombre": "Gestión Municipal y Participación",
             "definicion": "Opiniones sobre cómo funciona el municipio y cómo se involucra a la comunidad en las decisiones.",
             "criterios_inclusion": "Transparencia, trato a los vecinos, cercanía de las autoridades, información, espacios para participar, rol de las juntas de vecinos, uso de los recursos municipales.",
             "criterios_exclusion": "Reclamos por servicios concretos como basura o salud (el ámbito que corresponda) y propuestas de obras (Propuestas de Proyectos)."},
            {"nombre": "Propuestas de Proyectos",
             "definicion": "Ideas concretas que los vecinos proponen para la comuna, con algo específico que construir, crear o cambiar.",
             "criterios_inclusion": "\"Propongo un…\", \"construir…\", \"habilitar…\", programas con nombre o lugar identificable, soluciones detalladas a un problema.",
             "criterios_exclusion": "Problemas o carencias sin una solución propuesta (Desarrollo Social y Comunitario, Desarrollo Territorial y Medio Ambiente o Desarrollo Económico y Empleo, según el tema) y peticiones genéricas como \"más seguridad\"."},
        ],
    },
    "municipal_presupuesto_participativo": {
        "nombre": "Presupuesto Participativo",
        "industria": "Municipal",
        "palabras_clave": ["presupuesto", "participativo", "votacion", "votar", "priorizar", "postular", "junta", "iniciativa"],
        "descripcion": "Para procesos de presupuesto participativo: qué proyectos proponen y priorizan los vecinos, y qué opinan de las reglas y de la transparencia del proceso.",
        "marco_teorico": (
            "En un presupuesto participativo, los vecinos deciden en qué se gasta una parte del dinero del "
            "municipio. Esta plantilla separa tres cosas: las ideas de proyectos que presenta la comunidad "
            "(por tipo de proyecto), las razones por las que priorizan unos sobre otros, y la opinión sobre "
            "cómo funciona el proceso, sus reglas y la confianza en que se cumpla lo votado."
        ),
        "categorias_default": [
            {"nombre": "Proyectos de Infraestructura y Espacios Públicos",
             "definicion": "Propuestas de obras físicas para el barrio: plazas, veredas, luminarias, sedes y equipamiento.",
             "criterios_inclusion": "Mejoramiento de plazas y canchas, luminarias, veredas, paraderos, sedes vecinales, juegos infantiles, accesibilidad, pavimentación.",
             "criterios_exclusion": "Proyectos de seguridad que no son obras, como alarmas o rondas (Proyectos de Seguridad y Prevención), y actividades para las personas (Proyectos Sociales, Culturales y Deportivos)."},
            {"nombre": "Proyectos Sociales, Culturales y Deportivos",
             "definicion": "Propuestas de actividades, talleres y programas para personas y organizaciones.",
             "criterios_inclusion": "Talleres, eventos culturales, escuelas deportivas, apoyo a adultos mayores, actividades para niños y jóvenes, equipamiento de clubes y juntas de vecinos, fondos para organizaciones.",
             "criterios_exclusion": "Construcción de espacios físicos (Proyectos de Infraestructura y Espacios Públicos) y proyectos de seguridad (Proyectos de Seguridad y Prevención)."},
            {"nombre": "Proyectos de Seguridad y Prevención",
             "definicion": "Propuestas para que el barrio esté más seguro: vigilancia, iluminación con fines de seguridad y prevención.",
             "criterios_inclusion": "Cámaras, alarmas comunitarias, rejas, más patrullajes, programas de prevención del delito y del consumo de drogas, iluminación para prevenir delitos.",
             "criterios_exclusion": "Mejoras de espacios públicos sin foco en seguridad (Proyectos de Infraestructura y Espacios Públicos) y talleres para jóvenes (Proyectos Sociales, Culturales y Deportivos)."},
            {"nombre": "Criterios para Priorizar",
             "definicion": "Razones que dan los vecinos para elegir o preferir unos proyectos sobre otros.",
             "criterios_inclusion": "\"A cuántos beneficia\", urgencia, riesgo, abandono del sector, equidad entre barrios, costo, quiénes más lo necesitan.",
             "criterios_exclusion": "El proyecto propuesto en sí (la categoría de proyectos que corresponda) y críticas a las reglas de votación (Reglas y Confianza en el Proceso)."},
            {"nombre": "Reglas y Confianza en el Proceso",
             "definicion": "Opiniones sobre cómo se organiza la votación, qué tan justo es y si se confía en que el municipio cumplirá.",
             "criterios_inclusion": "Difusión, plazos, forma de votar, requisitos para postular, transparencia del conteo, \"nunca se hacen los proyectos\", bajo conocimiento del proceso, valoración de poder decidir.",
             "criterios_exclusion": "Reclamos por la mantención de la comuna en general (la categoría de proyectos que corresponda) y razones para elegir un proyecto (Criterios para Priorizar)."},
        ],
    },
}


def list_templates() -> list[dict]:
    return [
        {"key": key, "nombre": t["nombre"], "descripcion": t["descripcion"],
         "industria": t.get("industria", "General"),
         "n_categorias": len(t["categorias_default"]),
         "marco_teorico": t["marco_teorico"]}
        for key, t in FRAMEWORK_TEMPLATES.items()
    ]


def get_template(key: str) -> Optional[dict]:
    return FRAMEWORK_TEMPLATES.get(key)
