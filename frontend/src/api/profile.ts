import { apiRequest } from "./client";

export type CandidateProfileDto = {
  id: number | null;
  full_name: string;
  email: string;
  location: string;
  target_roles: string[];
  preferred_locations: string[];
  remote_preference: string;
  salary_expectation: string;
  availability: string;
  skills: string[];
  tech_stack: string[];
  projects: string[];
  experience_summary: string;
  education_summary: string;
  strengths: string[];
  no_gos: string[];
  application_tone: string;
  extra_context: string;
  created_at: string | null;
  updated_at: string | null;
};

export type CandidateProfilePayload = Omit<
  CandidateProfileDto,
  "id" | "created_at" | "updated_at"
>;

export function getCandidateProfile() {
  return apiRequest<CandidateProfileDto>("/api/profile/");
}

export function updateCandidateProfile(payload: CandidateProfilePayload) {
  return apiRequest<CandidateProfileDto>("/api/profile/", {
    method: "PATCH",
    body: payload,
  });
}
