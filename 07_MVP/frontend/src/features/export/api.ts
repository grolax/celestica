import { downloadFile } from "@/shared/api/client";
import { ClosedOpciones } from "@/features/analysis/types";
import { closedQuery, qp } from "@/features/analysis/api";

export const exportApi = {
  downloadPdf: (id: string, pregunta: string, includeDetails = true) =>
    downloadFile(`/projects/${id}/export/pdf?include_details=${includeDetails}&${qp(pregunta)}`),
  downloadDocx: (id: string, pregunta: string, includeDetails = true) =>
    downloadFile(`/projects/${id}/export/docx?include_details=${includeDetails}&${qp(pregunta)}`),
  downloadCsv: (id: string, pregunta: string) => downloadFile(`/projects/${id}/export/csv?${qp(pregunta)}`),
  downloadXlsx: (id: string, pregunta: string) => downloadFile(`/projects/${id}/export/xlsx?${qp(pregunta)}`),
  downloadClosedXlsx: (id: string, o?: ClosedOpciones) => downloadFile(`/projects/${id}/export/closed-xlsx${closedQuery(o)}`),
};
