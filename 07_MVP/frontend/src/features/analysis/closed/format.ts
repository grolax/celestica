export const num = (n: number, max = 2) => n.toLocaleString("es-CL", { maximumFractionDigits: max }).replace("-", "−");
export const pct = (n: number) => `${n.toLocaleString("es-CL", { minimumFractionDigits: 1, maximumFractionDigits: 1 })} %`;
export const conN = (x: { n: number; pct: number }) => `${pct(x.pct)} (${num(x.n, 0)})`;
export const valores = (v: number[]) => v.join(" y ");
