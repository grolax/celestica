import { jsonBody, req } from "@/shared/api/client";

export interface QualtricsStatus {
  configured: boolean;
  datacenter: string;
}

export interface QualtricsSurvey {
  id: string;
  name: string;
}

export interface ImportResult {
  id: string;
  n_responses: number;
  text_column: string;
}

interface ImportCommon {
  name: string;
  marco_teorico: string;
  template: string;
}

export const integrationsApi = {
  // Credenciales Qualtrics (el token nunca vuelve al navegador)
  qualtricsStatus: () => req<QualtricsStatus>("/integrations/qualtrics/credentials"),
  qualtricsSaveCredentials: (api_token: string, datacenter: string) =>
    req<QualtricsStatus>("/integrations/qualtrics/credentials", { method: "PUT", ...jsonBody({ api_token, datacenter }) }),
  qualtricsDeleteCredentials: () =>
    req<QualtricsStatus>("/integrations/qualtrics/credentials", { method: "DELETE" }),

  // Importación
  qualtricsSurveys: () => req<QualtricsSurvey[]>("/integrations/qualtrics/surveys"),
  createFromQualtrics: (body: ImportCommon & { survey_id: string; survey_name: string }) =>
    req<ImportResult>("/projects/from-qualtrics", { method: "POST", ...jsonBody(body) }),
  createFromGoogleForms: (body: ImportCommon & { sheet_url: string }) =>
    req<ImportResult>("/projects/from-google-forms", { method: "POST", ...jsonBody(body) }),
};
