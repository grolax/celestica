import { req } from "@/shared/api/client";
import { ClaudeUsage, ClaudeUsageTotals } from "@/features/analysis/types";

export interface PromptEntry {
  label: string;
  description: string;
  system: string;
  instructions: string;
}

export type PromptsData = Record<string, PromptEntry>;

export interface UsageProject {
  id: string;
  name: string;
  user_id: string;
  created_at: string;
  n_responses: number;
  claude_usage: ClaudeUsage;
}

export interface AdminHealth {
  thematic_version: string;
  model: string;
  model_report_v2: string;
  model_max_output_tokens: Record<string, number> | null;
  synthesis_batch_input_tokens: number;
  merge_input_tokens: number;
  large_output_tokens: number;
  v2_max_workers: number;
  log_dir: string;
}

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
  getUsage: (password: string) =>
    req<{ projects: UsageProject[]; total: ClaudeUsageTotals; log_dir: string }>("/admin/usage", {
      headers: { "X-Admin-Password": password },
    }),
  getHealth: (password: string) =>
    req<AdminHealth>("/admin/health", { headers: { "X-Admin-Password": password } }),
};
