import Card from "@/shared/components/Card";
import PageHeader from "@/shared/components/PageHeader";

export default function Documentation() {
  return (
    <div style={{ maxWidth: 820 }}>
      <PageHeader title="Documentación" help="Guía de uso y explicación de cada concepto de la plataforma." />

      <Card title="¿Qué es Celestica?">
        <p>
          Celestica automatiza el análisis cualitativo de encuestas abiertas (evaluación docente,
          acreditación, satisfacción) manteniendo el rigor metodológico: la IA propone, tu equipo decide,
          y toda decisión queda registrada para auditoría CNA/CNE.
        </p>
      </Card>

      <Card title="Flujo de trabajo recomendado">
        <ol style={{ paddingLeft: 20, lineHeight: 2 }}>
          <li><strong>Crear proyecto:</strong> sube un CSV/XLSX con respuestas abiertas y define el marco teórico (o parte de una plantilla CNA).</li>
          <li><strong>Análisis léxico (Capa 1):</strong> frecuencias, bigramas y sentimiento. Determinístico, en segundos.</li>
          <li><strong>Libro de códigos (Capa 2):</strong> la IA propone categorías ancladas al marco; tu equipo valida, edita o descarta cada una. Usa los comentarios para discutir con colegas.</li>
          <li><strong>Codificación:</strong> Claude codifica el corpus contra las categorías validadas con justificación y confianza. Revisa las asignaciones de confianza baja y re-codifica donde corresponda.</li>
          <li><strong>Trazabilidad:</strong> revisa la tabla completa respuesta → categoría → justificación → fuente.</li>
          <li><strong>Informe:</strong> genera la lectura interpretativa (hipótesis, tensiones, preguntas).</li>
          <li><strong>Exportar:</strong> PDF/Word con trazabilidad para archivos de acreditación; CSV/Excel para análisis propio.</li>
        </ol>
      </Card>

      <Card title="Sobre el indicador de confianza">
        <p className="muted">
          La confianza (0.0–1.0) estima qué tan bien encaja una respuesta en su categoría. Es orientativa:
          sirve para priorizar revisión manual, no para excluir datos automáticamente.
          <span className="conf-badge conf-high">≥ 0.85 Alta</span>
          <span className="conf-badge conf-mid">0.60–0.84 Media</span>
          <span className="conf-badge conf-low">&lt; 0.60 Baja</span>
        </p>
      </Card>

      <Card title="Preparación del archivo de datos">
        <p className="muted">
          El archivo debe tener al menos una columna con las respuestas abiertas. Si hay varias columnas,
          Celestica detecta automáticamente la de texto (mayor largo promedio). Una columna
          <code>id_respuesta</code> opcional permite conservar tus identificadores. El resto de las columnas
          se guarda como metadata de cada respuesta.
        </p>
      </Card>

      <Card title="Soporte">
        <p className="muted" style={{ margin: 0 }}>
          ¿Dudas o problemas? Escríbenos a <a href="mailto:soporte@softinsight.cl">soporte@softinsight.cl</a> —
          respondemos en español y conocemos el contexto institucional chileno.
        </p>
      </Card>
    </div>
  );
}
