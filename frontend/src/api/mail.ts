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
  sender: string;
  subject: string;
  body: string;
  received_at: string;
  classification: EmailClassification;
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
