import { apiRequest } from "./client";

export type EmailClassification =
  | "confirmation"
  | "rejection"
  | "invitation"
  | "question"
  | "follow_up"
  | "unknown"
  | "requires_action";

export type EmailMessageDto = {
  id: number;
  application: number | null;
  application_summary: {
    id: number;
    company: string;
    title: string;
    status: string;
  } | null;
  application_company: string;
  application_job_title: string;
  sender: string;
  subject: string;
  body: string;
  received_at: string;
  classification: EmailClassification;
  requires_action: boolean;
  created_at: string;
};

export function getMailMessages() {
  return apiRequest<EmailMessageDto[]>("/api/mail/messages/");
}

export function syncMail() {
  return apiRequest<{ message: string; created_messages: number; message_ids: number[] }>(
    "/api/mail/sync/",
    { method: "POST" },
  );
}

export function classifyMailMessage(messageId: number) {
  return apiRequest<EmailMessageDto>(`/api/mail/messages/${messageId}/classify/`, {
    method: "POST",
  });
}

export function updateMailMessage(
  messageId: number,
  payload: { application: number | null },
) {
  return apiRequest<EmailMessageDto>(`/api/mail/messages/${messageId}/`, {
    method: "PATCH",
    body: payload,
  });
}
