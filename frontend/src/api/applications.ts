import { apiRequest } from "./client";

export type ApplicationStatus =
  | "new"
  | "interesting"
  | "draft_open"
  | "draft_approved"
  | "gmail_draft_created"
  | "applied"
  | "response_received"
  | "interview"
  | "rejected"
  | "follow_up_due"
  | "closed";

export type ApplicationDocumentDto = {
  id: number;
  application: number;
  document_type: "cover_letter" | "email" | "follow_up" | "reply";
  title: string;
  content: string;
  version: number;
  is_approved: boolean;
  created_at: string;
  updated_at: string;
};

export type ApplicationDto = {
  id: number;
  job: number;
  job_detail: {
    id: number;
    company: string;
    title: string;
    location: string;
    remote_type: string;
  };
  match_score: number | null;
  status: ApplicationStatus;
  notes: string;
  applied_at: string | null;
  follow_up_at: string | null;
  created_at: string;
  updated_at: string;
  documents: ApplicationDocumentDto[];
  status_events: Array<{
    id: number;
    application: number;
    old_status: string;
    new_status: string;
    note: string;
    created_at: string;
  }>;
};

export type UpdateApplicationPayload = Partial<
  Pick<ApplicationDto, "status" | "notes" | "follow_up_at">
>;

export function getApplications() {
  return apiRequest<ApplicationDto[]>("/api/applications/");
}

export function getApplication(applicationId: number) {
  return apiRequest<ApplicationDto>(`/api/applications/${applicationId}/`);
}

export function updateApplication(
  applicationId: number,
  payload: UpdateApplicationPayload,
) {
  return apiRequest<ApplicationDto>(`/api/applications/${applicationId}/`, {
    method: "PATCH",
    body: payload,
  });
}

export function markApplicationApplied(applicationId: number) {
  return apiRequest<ApplicationDto>(`/api/applications/${applicationId}/mark-applied/`, {
    method: "POST",
  });
}

export function generateApplicationDocuments(applicationId: number) {
  return apiRequest<ApplicationDocumentDto[]>(
    `/api/applications/${applicationId}/generate-documents/`,
    { method: "POST" },
  );
}

export function generateFollowUpDocument(applicationId: number) {
  return apiRequest<ApplicationDocumentDto>(
    `/api/applications/${applicationId}/generate-follow-up/`,
    { method: "POST" },
  );
}

export function updateApplicationDocument(
  applicationId: number,
  documentId: number,
  payload: Pick<ApplicationDocumentDto, "title" | "content">,
) {
  return apiRequest<ApplicationDocumentDto>(
    `/api/applications/${applicationId}/documents/${documentId}/`,
    {
      method: "PATCH",
      body: payload,
    },
  );
}

export function approveApplicationDocument(applicationId: number, documentId: number) {
  return apiRequest<ApplicationDocumentDto>(
    `/api/applications/${applicationId}/approve-document/`,
    {
      method: "POST",
      body: { document_id: documentId },
    },
  );
}

export function createGmailDraft(applicationId: number) {
  return apiRequest<{ message: string; draft_subject: string }>(
    `/api/applications/${applicationId}/create-gmail-draft/`,
    { method: "POST" },
  );
}
