import { apiRequest } from "./client";
import type { ApplicationDto } from "./applications";

export type JobMatchDto = {
  id: number;
  job: number;
  score: number;
  category: "A" | "B" | "C" | "X";
  strengths: string[];
  risks: string[];
  recommendation: string;
  application_angle: string;
  created_at: string;
};

export type JobPostingDto = {
  id: number;
  company: string;
  title: string;
  location: string;
  source: string;
  source_url: string;
  description: string;
  requirements: string[];
  nice_to_have: string[];
  tags: string[];
  employment_type: string;
  remote_type: string;
  published_at: string | null;
  created_at: string;
  updated_at: string;
  match?: JobMatchDto | null;
};

export type ManualJobPostingPayload = {
  company: string;
  title: string;
  location: string;
  source: string;
  source_url: string;
  description: string;
  requirements: string[];
  nice_to_have: string[];
  tags: string[];
  employment_type: string;
  remote_type: string;
};

export function getJobs() {
  return apiRequest<JobPostingDto[]>("/api/jobs/");
}

export function createManualJobPosting(payload: ManualJobPostingPayload) {
  return apiRequest<JobPostingDto>("/api/jobs/manual-import/", {
    method: "POST",
    body: payload,
  });
}

export function evaluateJob(jobId: number) {
  return apiRequest<JobMatchDto>(`/api/jobs/${jobId}/evaluate/`, {
    method: "POST",
  });
}

export function createApplicationForJob(jobId: number) {
  return apiRequest<ApplicationDto>(`/api/jobs/${jobId}/create-application/`, {
    method: "POST",
  });
}
