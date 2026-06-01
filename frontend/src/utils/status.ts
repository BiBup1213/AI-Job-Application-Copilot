import type {
  ApplicationDocumentDto,
  ApplicationDto,
  ApplicationStatus,
} from "../api/applications";
import type { EmailClassification, EmailMessageDto } from "../api/mail";
import type { StatusTone } from "../mockDashboardData";
import { daysSince, isFollowUpDue } from "./date";
import { titleCase } from "./text";

export const followUpIntervalDays = 7;

export type FollowUpFilterKey = "all" | "due" | "planned" | "without_date" | "done";

export function applicationStatusLabel(status: ApplicationStatus) {
  const labels: Record<ApplicationStatus, string> = {
    new: "Neu gefunden",
    interesting: "Interessant",
    draft_open: "Entwurf offen",
    draft_approved: "Entwurf freigegeben",
    gmail_draft_created: "Gmail-Entwurf",
    applied: "Beworben",
    response_received: "Antwort erhalten",
    interview: "Interview",
    rejected: "Absage",
    follow_up_due: "Follow-up fällig",
    closed: "Geschlossen",
  };
  return labels[status];
}

export function applicationStatusText(status: string) {
  if (isApplicationStatus(status)) return applicationStatusLabel(status);
  return status || "Unbekannt";
}

export function isApplicationStatus(status: string): status is ApplicationStatus {
  return [
    "new",
    "interesting",
    "draft_open",
    "draft_approved",
    "gmail_draft_created",
    "applied",
    "response_received",
    "interview",
    "rejected",
    "follow_up_due",
    "closed",
  ].includes(status);
}

export function applicationStatusTone(status: ApplicationStatus): StatusTone {
  if (["applied", "interview", "draft_approved", "gmail_draft_created"].includes(status)) {
    return "green";
  }
  if (["draft_open", "follow_up_due", "interesting"].includes(status)) {
    return "orange";
  }
  if (status === "rejected" || status === "closed") return "red";
  if (status === "response_received") return "blue";
  return "orange";
}

export function nextActionForStatus(status?: ApplicationStatus) {
  if (!status || status === "new" || status === "interesting") return "Bewerbung erstellen";
  if (status === "draft_open") return "Entwurf prüfen";
  if (status === "draft_approved") return "Gmail-Entwurf erstellen";
  if (status === "gmail_draft_created") return "Versand manuell prüfen";
  if (status === "applied") return "Antwort abwarten";
  if (status === "follow_up_due") return "Follow-up senden";
  if (status === "response_received") return "Antwort prüfen";
  if (status === "interview") return "Termin vorbereiten";
  return "Details ansehen";
}

export function classificationLabel(classification: EmailClassification) {
  const labels: Record<EmailClassification, string> = {
    confirmation: "Eingangsbestätigung",
    rejection: "Absage erkannt",
    invitation: "Einladung",
    question: "Antwort erforderlich",
    follow_up: "Follow-up",
    unknown: "Unbekannt",
    requires_action: "Antwort erforderlich",
  };
  return labels[classification];
}

export function classificationTone(classification: EmailClassification): StatusTone {
  if (classification === "confirmation" || classification === "invitation") return "green";
  if (classification === "question" || classification === "requires_action") return "orange";
  if (classification === "rejection") return "red";
  return "gray";
}

export function suggestedMailAction(classification: EmailClassification) {
  const suggestions: Record<EmailClassification, string> = {
    confirmation: "Als beworben bestätigen",
    rejection: "Als Absage markieren",
    invitation: "Als Gespräch markieren",
    question: "Antwort erforderlich",
    follow_up: "Follow-up prüfen",
    unknown: "Bitte manuell prüfen und bei Bedarf neu klassifizieren.",
    requires_action: "Antwort erforderlich",
  };
  return suggestions[classification];
}

export function suggestedApplicationStatus(
  classification: EmailClassification,
): ApplicationStatus | null {
  const statuses: Partial<Record<EmailClassification, ApplicationStatus>> = {
    confirmation: "applied",
    rejection: "rejected",
    invitation: "interview",
    question: "response_received",
    follow_up: "follow_up_due",
    requires_action: "response_received",
  };
  return statuses[classification] ?? null;
}

export function canCreateReplyDraft(classification: EmailClassification) {
  return classification === "question" || classification === "invitation";
}

export function displaySender(sender: string) {
  if (!sender.includes("@")) return sender;
  return titleCase(sender.split("@")[0].replace(/[._-]/g, " "));
}

export function latestMailForApplication(
  applicationId: number,
  mailMessages: EmailMessageDto[],
) {
  return (
    mailMessages
      .filter((message) => message.application === applicationId)
      .sort(
        (first, second) =>
          new Date(second.received_at).getTime() -
          new Date(first.received_at).getTime(),
      )[0] ?? null
  );
}

export function isFollowUpRelevant(
  application: ApplicationDto,
  mailMessages: EmailMessageDto[],
) {
  if (application.status === "closed" || application.status === "rejected") return false;
  return (
    application.status === "applied" ||
    application.status === "follow_up_due" ||
    Boolean(application.follow_up_at) ||
    isApplicationFollowUpDue(
      application,
      latestMailForApplication(application.id, mailMessages),
    )
  );
}

export function matchesFollowUpFilter(
  application: ApplicationDto,
  filter: FollowUpFilterKey,
  mailMessages: EmailMessageDto[],
) {
  const latestMail = latestMailForApplication(application.id, mailMessages);
  if (filter === "all") return true;
  if (filter === "due") return isApplicationFollowUpDue(application, latestMail);
  if (filter === "planned") return isFollowUpPlanned(application);
  if (filter === "without_date") {
    return application.status === "applied" && !application.follow_up_at;
  }
  return (
    application.status === "applied" &&
    !isApplicationFollowUpDue(application, latestMail)
  );
}

export function isApplicationFollowUpDue(
  application: ApplicationDto,
  latestMail: EmailMessageDto | null,
) {
  if (application.status === "follow_up_due") return true;
  if (isFollowUpDue(application.follow_up_at)) return true;
  const hasResponse = latestMail
    ? ["question", "invitation", "rejection", "follow_up", "requires_action"].includes(
        latestMail.classification,
      )
    : false;
  return (
    application.status === "applied" &&
    !application.follow_up_at &&
    !hasResponse &&
    daysSince(application.applied_at) >= followUpIntervalDays
  );
}

export function isFollowUpPlanned(application: ApplicationDto) {
  if (!application.follow_up_at) return false;
  const followUpDate = new Date(application.follow_up_at);
  const today = new Date();
  followUpDate.setHours(0, 0, 0, 0);
  today.setHours(0, 0, 0, 0);
  return followUpDate.getTime() > today.getTime();
}

export function latestDocumentOfType(
  application: ApplicationDto,
  documentType: ApplicationDocumentDto["document_type"],
) {
  return (
    application.documents
      .filter((document) => document.document_type === documentType)
      .sort((first, second) => second.version - first.version)[0] ?? null
  );
}
