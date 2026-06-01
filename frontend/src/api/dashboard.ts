import { apiRequest } from "./client";

export type DashboardSummary = {
  kpis: {
    new_matching_jobs: number;
    open_drafts: number;
    applied_count: number;
    responses_count: number;
    followups_due: number;
  };
  jobs_total: number;
  applications_total: number;
  applications_by_status: Record<string, number>;
  emails_requiring_attention: number;
  top_matches: Array<{
    job_id: number;
    company: string;
    title: string;
    score: number;
    category: string;
  }>;
  next_actions: string[];
};

export function getDashboardSummary() {
  return apiRequest<DashboardSummary>("/api/dashboard/summary/");
}
