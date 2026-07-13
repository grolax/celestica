/** Render del informe: detecta títulos (líneas cortas en mayúsculas) y párrafos. */
export default function ReportBody({ text }: { text: string }) {
  const blocks = text.split(/\n{2,}/).map((block, i) => {
    const trimmed = block.trim();
    if (!trimmed) return null;
    const isHeading = trimmed.length < 80 && trimmed === trimmed.toUpperCase() && /[A-ZÁÉÍÓÚÑ]/.test(trimmed);
    return isHeading
      ? <h3 key={i}>{trimmed}</h3>
      : <p key={i} className="report-paragraph">{trimmed}</p>;
  });

  return <div className="report-body">{blocks}</div>;
}
