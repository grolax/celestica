import { downloadFile } from "@/shared/api/client";

export const exportApi = {
  downloadPdf: (id: string, includeDetails = true) =>
    downloadFile(`/projects/${id}/export/pdf?include_details=${includeDetails}`),
  downloadDocx: (id: string, includeDetails = true) =>
    downloadFile(`/projects/${id}/export/docx?include_details=${includeDetails}`),
  downloadCsv: (id: string) => downloadFile(`/projects/${id}/export/csv`),
  downloadXlsx: (id: string) => downloadFile(`/projects/${id}/export/xlsx`),
};
