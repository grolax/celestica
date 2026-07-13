import { req } from "@/shared/api/client";

export interface PromptEntry {
  label: string;
  description: string;
  system: string;
  instructions: string;
}

export type PromptsData = Record<string, PromptEntry>;

export const adminApi = {
  getPrompts: (password: string) =>
    req<{ prompts: PromptsData; defaults: PromptsData }>("/admin/prompts", {
      headers: { "X-Admin-Password": password },
    }),
  updatePrompt: (password: string, key: string, body: { system: string; instructions: string }) =>
    req<PromptEntry>(`/admin/prompts/${key}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json", "X-Admin-Password": password },
      body: JSON.stringify(body),
    }),
  resetPrompt: (password: string, key: string) =>
    req<PromptEntry>(`/admin/prompts/${key}/reset`, {
      method: "POST", headers: { "X-Admin-Password": password },
    }),
};
