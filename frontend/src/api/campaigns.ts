import { apiRequest } from "./client";

export type SearchCampaignDto = {
  id: number;
  name: string;
  keywords: string[];
  industries: string[];
  sources: string[];
  location: string;
  radius_km: number;
  remote_allowed: boolean;
  hybrid_allowed: boolean;
  exclude_keywords: string[];
  status: "draft" | "active" | "paused" | "completed";
  created_at: string;
  updated_at: string;
};

export type CreateCampaignPayload = Pick<
  SearchCampaignDto,
  | "name"
  | "keywords"
  | "industries"
  | "sources"
  | "location"
  | "radius_km"
  | "remote_allowed"
  | "hybrid_allowed"
  | "exclude_keywords"
> & {
  status?: SearchCampaignDto["status"];
};

export function getCampaigns() {
  return apiRequest<SearchCampaignDto[]>("/api/campaigns/");
}

export function createCampaign(payload: CreateCampaignPayload) {
  return apiRequest<SearchCampaignDto>("/api/campaigns/", {
    method: "POST",
    body: payload,
  });
}

export function runCampaign(campaignId: number) {
  return apiRequest<{ message: string; created_jobs: number; job_ids: number[] }>(
    `/api/campaigns/${campaignId}/run/`,
    { method: "POST" },
  );
}
