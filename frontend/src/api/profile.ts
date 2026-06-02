import { API_BASE_URL, ApiError, apiRequest } from "./client";

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

export type CandidateDocumentType =
  | "cv"
  | "certificate"
  | "reference"
  | "cover_letter_template"
  | "other";

export type CandidateDocumentExtractionStatus =
  | "pending"
  | "success"
  | "failed"
  | "unsupported";

export type CandidateDocumentDto = {
  id: number;
  profile: number | null;
  document_type: CandidateDocumentType;
  title: string;
  file_url: string;
  original_filename: string;
  content_type: string;
  file_size: number;
  extracted_text: string;
  extracted_text_length: number;
  extraction_error: string;
  extraction_status: CandidateDocumentExtractionStatus;
  use_for_ai_context: boolean;
  notes: string;
  created_at: string;
  updated_at: string;
};

export type CandidateProfileSuggestionData = {
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
  confidence_notes: string[];
  missing_information: string[];
  _meta?: {
    provider_used?: "mock" | "openai" | string;
    fallback_used?: boolean;
    fallback_reason?: string;
    source_text_length?: number;
    document_count?: number;
  };
};

export type CandidateProfileSuggestionDto = {
  id: number;
  profile: number | null;
  source_documents: CandidateDocumentDto[];
  source_document_ids: number[];
  suggested_data: CandidateProfileSuggestionData;
  status: "draft" | "applied" | "dismissed";
  created_at: string;
  updated_at: string;
  applied_at: string | null;
};

export type UploadCandidateDocumentPayload = {
  document_type: CandidateDocumentType;
  title: string;
  file: File;
};

export type UpdateCandidateDocumentPayload = Partial<
  Pick<
    CandidateDocumentDto,
    "document_type" | "title" | "extracted_text" | "use_for_ai_context" | "notes"
  >
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

export function getCandidateDocuments() {
  return apiRequest<CandidateDocumentDto[]>("/api/profile/documents/");
}

export function getCandidateDocument(documentId: number) {
  return apiRequest<CandidateDocumentDto>(`/api/profile/documents/${documentId}/`);
}

export function uploadCandidateDocument(payload: UploadCandidateDocumentPayload) {
  const formData = new FormData();
  formData.append("document_type", payload.document_type);
  formData.append("title", payload.title);
  formData.append("file", payload.file);
  return multipartRequest<CandidateDocumentDto>("/api/profile/documents/", {
    method: "POST",
    body: formData,
  });
}

export function updateCandidateDocument(
  documentId: number,
  payload: UpdateCandidateDocumentPayload,
) {
  return apiRequest<CandidateDocumentDto>(`/api/profile/documents/${documentId}/`, {
    method: "PATCH",
    body: payload,
  });
}

export function deleteCandidateDocument(documentId: number) {
  return apiRequest<void>(`/api/profile/documents/${documentId}/`, {
    method: "DELETE",
  });
}

export function reextractCandidateDocument(documentId: number) {
  return apiRequest<CandidateDocumentDto>(
    `/api/profile/documents/${documentId}/reextract/`,
    { method: "POST" },
  );
}

export function suggestProfileFromDocuments(documentIds?: number[]) {
  return apiRequest<CandidateProfileSuggestionDto>("/api/profile/suggest-from-documents/", {
    method: "POST",
    body: documentIds?.length ? { document_ids: documentIds } : {},
  });
}

export function getProfileSuggestions() {
  return apiRequest<CandidateProfileSuggestionDto[]>("/api/profile/suggestions/");
}

export function getProfileSuggestion(suggestionId: number) {
  return apiRequest<CandidateProfileSuggestionDto>(
    `/api/profile/suggestions/${suggestionId}/`,
  );
}

export function applyProfileSuggestion(suggestionId: number) {
  return apiRequest<CandidateProfileSuggestionDto>(
    `/api/profile/suggestions/${suggestionId}/apply/`,
    { method: "POST" },
  );
}

export function dismissProfileSuggestion(suggestionId: number) {
  return apiRequest<CandidateProfileSuggestionDto>(
    `/api/profile/suggestions/${suggestionId}/dismiss/`,
    { method: "POST" },
  );
}

async function multipartRequest<T>(path: string, options: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, options);
  const contentType = response.headers.get("content-type") ?? "";
  const payload = contentType.includes("application/json")
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    const message = errorMessageFromPayload(payload);
    throw new ApiError(message, response.status, payload);
  }

  return payload as T;
}

function errorMessageFromPayload(payload: unknown) {
  if (typeof payload === "object" && payload !== null) {
    if ("detail" in payload) return String((payload as { detail: unknown }).detail);
    const firstValue = Object.values(payload)[0];
    if (Array.isArray(firstValue) && firstValue.length) return String(firstValue[0]);
    if (typeof firstValue === "string") return firstValue;
  }
  return "Upload fehlgeschlagen.";
}
