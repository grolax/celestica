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
