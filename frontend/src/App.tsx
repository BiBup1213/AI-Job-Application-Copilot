import { useCallback, useEffect, useMemo, useState } from "react";
import type { FormEvent, MouseEvent, ReactNode } from "react";
import { Navigate, NavLink, Route, Routes, useNavigate, useParams } from "react-router-dom";
import {
  ArrowRight,
  Bell,
  Bookmark,
  BriefcaseBusiness,
  Check,
  ChevronDown,
  ChevronRight,
  ExternalLink,
  FileText,
  Loader2,
  Mail,
  MoreVertical,
  PenLine,
  Plus,
  RefreshCw,
  Search,
  Send,
  Sparkles,
  TriangleAlert,
  X,
  type LucideIcon,
} from "lucide-react";
import {
  approveApplicationDocument,
  createGmailDraft,
  generateApplicationDocuments,
  generateFollowUpDocument,
  getApplication,
  getApplications,
  markApplicationApplied,
  updateApplication,
  updateApplicationDocument,
  type ApplicationDto,
  type ApplicationDocumentDto,
  type ApplicationStatus,
  type UpdateApplicationPayload,
} from "./api/applications";
import {
  createCampaign,
  getCampaigns,
  runCampaign,
  type SearchCampaignDto,
} from "./api/campaigns";
import { ApiError } from "./api/client";
import { getDashboardSummary, type DashboardSummary } from "./api/dashboard";
import {
  createApplicationForJob,
  createManualJobPosting,
  getJobs,
  type ManualJobPostingPayload,
  type JobPostingDto,
} from "./api/jobs";
import {
  classifyMailMessage,
  getMailMessages,
  syncMail,
  updateMailMessage,
  type EmailMessageDto,
} from "./api/mail";
import {
  navigationItems,
  type Job,
  type Kpi,
  type StatusTone,
} from "./mockDashboardData";
import {
  dateInputToDateTime,
  dateInputValue,
  daysSinceDate,
  formatDate,
  formatNullableDate,
  isFollowUpDue,
  relativeDate,
} from "./utils/date";
import {
  applicationStatusLabel,
  applicationStatusText,
  applicationStatusTone,
  canCreateReplyDraft,
  classificationLabel,
  classificationTone,
  displaySender,
  isApplicationFollowUpDue,
  isFollowUpRelevant,
  latestDocumentOfType,
  latestMailForApplication,
  matchesFollowUpFilter,
  nextActionForStatus,
  suggestedApplicationStatus,
  suggestedMailAction,
  type FollowUpFilterKey,
} from "./utils/status";
import { initialsFrom, logoForCompany, splitCsv, titleCase } from "./utils/text";

type ActionState =
  | "idle"
  | "creating-application"
  | "creating-draft"
  | "syncing-mail"
  | "creating-campaign"
  | "importing-job";

type Notice = {
  type: "success" | "error";
  text: string;
};

type CampaignFormState = {
  name: string;
  keywords: string;
  industries: string;
  sources: string[];
  location: string;
  radius_km: number;
  remote_allowed: boolean;
  hybrid_allowed: boolean;
  exclude_keywords: string;
};

type ManualJobFormState = {
  company: string;
  title: string;
  location: string;
  source: string;
  source_url: string;
  employment_type: string;
  remote_type: string;
  description: string;
  requirements: string;
  nice_to_have: string;
  tags: string;
};

type DisplayCampaign = {
  id: number;
  title: string;
  meta: string;
  sources: string[];
  count: string;
};

type DisplayMail = {
  id: number;
  sender: string;
  subject: string;
  badge: string;
  tone: StatusTone;
  initials: string;
};

type PipelineColumn = {
  title: string;
  count: number;
  tone: "blue" | "orange" | "green" | "purple";
  cards: Array<{ id: number; title: string; subtitle: string; date: string }>;
};

type TodayItem = {
  title: string;
  subtitle: string;
  count: number;
  icon: LucideIcon;
  path?: string;
};

type ReviewDocumentType = "cover_letter" | "email";
type ApplicationFilterKey =
  | "all"
  | "draft"
  | "approved"
  | "gmail"
  | "applied"
  | "response"
  | "interview"
  | "rejected"
  | "follow_up"
  | "closed";
type MailFilterKey =
  | "all"
  | "requires_action"
  | "confirmation"
  | "question"
  | "invitation"
  | "rejection"
  | "unknown";

function cn(...classes: Array<string | false | null | undefined>) {
  return classes.filter(Boolean).join(" ");
}

const toneStyles: Record<StatusTone, string> = {
  blue: "bg-blue-50 text-blue-700 border-blue-200",
  green: "bg-emerald-50 text-emerald-700 border-emerald-200",
  orange: "bg-orange-50 text-orange-700 border-orange-200",
  red: "bg-rose-50 text-rose-700 border-rose-200",
  gray: "bg-slate-50 text-slate-600 border-slate-200",
};

const dotStyles: Record<StatusTone, string> = {
  blue: "bg-blue-600",
  green: "bg-emerald-600",
  orange: "bg-amber-500",
  red: "bg-rose-500",
  gray: "bg-slate-400",
};

const campaignSources = [
  "Arbeitsagentur",
  "StepStone",
  "Indeed",
  "LinkedIn",
  "XING",
  "Unternehmensseiten",
  "Manuelle Eingabe",
];

const defaultCampaignForm: CampaignFormState = {
  name: "Python Entwickler (Junior)",
  keywords: "Python, Django, REST, Junior",
  industries: "Software, E-Commerce",
  sources: ["LinkedIn", "StepStone"],
  location: "Deutschland",
  radius_km: 50,
  remote_allowed: true,
  hybrid_allowed: true,
  exclude_keywords: "Senior, Lead",
};

const defaultManualJobForm: ManualJobFormState = {
  company: "",
  title: "",
  location: "",
  source: "Manuelle Eingabe",
  source_url: "",
  employment_type: "",
  remote_type: "",
  description: "",
  requirements: "",
  nice_to_have: "",
  tags: "",
};

const applicationFilters: Array<{
  key: ApplicationFilterKey;
  label: string;
  statuses: ApplicationStatus[];
}> = [
  { key: "all", label: "Alle", statuses: [] },
  { key: "draft", label: "Entwurf", statuses: ["draft_open"] },
  { key: "approved", label: "Freigegeben", statuses: ["draft_approved"] },
  { key: "gmail", label: "Gmail-Entwurf", statuses: ["gmail_draft_created"] },
  { key: "applied", label: "Beworben", statuses: ["applied"] },
  { key: "response", label: "Antwort", statuses: ["response_received"] },
  { key: "interview", label: "Gespräch", statuses: ["interview"] },
  { key: "rejected", label: "Absage", statuses: ["rejected"] },
  { key: "follow_up", label: "Follow-up", statuses: ["follow_up_due"] },
  { key: "closed", label: "Abgeschlossen", statuses: ["closed"] },
];

const mailFilters: Array<{
  key: MailFilterKey;
  label: string;
  predicate: (message: EmailMessageDto) => boolean;
}> = [
  { key: "all", label: "Alle", predicate: () => true },
  {
    key: "requires_action",
    label: "Aktion erforderlich",
    predicate: (message) => message.requires_action,
  },
  {
    key: "confirmation",
    label: "Eingangsbestätigung",
    predicate: (message) => message.classification === "confirmation",
  },
  {
    key: "question",
    label: "Rückfrage",
    predicate: (message) =>
      message.classification === "question" || message.classification === "requires_action",
  },
  {
    key: "invitation",
    label: "Einladung",
    predicate: (message) => message.classification === "invitation",
  },
  {
    key: "rejection",
    label: "Absage",
    predicate: (message) => message.classification === "rejection",
  },
  {
    key: "unknown",
    label: "Unbekannt",
    predicate: (message) => message.classification === "unknown",
  },
];

const followUpFilters: Array<{ key: FollowUpFilterKey; label: string }> = [
  { key: "all", label: "Alle" },
  { key: "due", label: "Fällig" },
  { key: "planned", label: "Geplant" },
  { key: "without_date", label: "Ohne Datum" },
  { key: "done", label: "Erledigt" },
];

export function App() {
  return (
    <div className="min-h-screen bg-[#f7f9fd] text-slate-950">
      <Sidebar />
      <main className="min-h-screen pl-[292px]">
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/suchkampagnen" element={<PlaceholderPage title="Suchkampagnen" />} />
          <Route path="/jobs" element={<JobsPage />} />
          <Route path="/bewerbungen/:id" element={<ApplicationReviewPage />} />
          <Route path="/bewerbungen" element={<ApplicationsPage />} />
          <Route path="/mail" element={<MailPage />} />
          <Route path="/follow-ups" element={<FollowUpsPage />} />
          <Route path="/profil" element={<PlaceholderPage title="Profil" />} />
          <Route path="/einstellungen" element={<PlaceholderPage title="Einstellungen" />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
}

function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [jobPostings, setJobPostings] = useState<JobPostingDto[]>([]);
  const [applications, setApplications] = useState<ApplicationDto[]>([]);
  const [campaigns, setCampaigns] = useState<SearchCampaignDto[]>([]);
  const [mailMessages, setMailMessages] = useState<EmailMessageDto[]>([]);
  const [selectedJobId, setSelectedJobId] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [notice, setNotice] = useState<Notice | null>(null);
  const [actionState, setActionState] = useState<ActionState>("idle");
  const [isCampaignModalOpen, setIsCampaignModalOpen] = useState(false);
  const [isManualJobModalOpen, setIsManualJobModalOpen] = useState(false);
  const [reviewApplication, setReviewApplication] = useState<ApplicationDto | null>(null);

  const loadData = useCallback(async () => {
    setIsLoading(true);
    setLoadError(null);
    try {
      const [dashboardData, jobsData, campaignsData, mailData, applicationsData] =
        await Promise.all([
          getDashboardSummary(),
          getJobs(),
          getCampaigns(),
          getMailMessages(),
          getApplications(),
        ]);
      setSummary(dashboardData);
      setJobPostings(jobsData);
      setCampaigns(campaignsData);
      setMailMessages(mailData);
      setApplications(applicationsData);
      setSelectedJobId((current) => current ?? jobsData[0]?.id ?? null);
    } catch (error) {
      setLoadError(readableError(error));
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  const displayJobs = useMemo(
    () => jobPostings.map((job) => mapJob(job, applications)),
    [applications, jobPostings],
  );
  const selectedJob =
    displayJobs.find((job) => job.apiId === selectedJobId) ?? displayJobs[0] ?? null;
  const kpis = useMemo(
    () => buildKpis(summary, jobPostings, applications, mailMessages),
    [applications, jobPostings, mailMessages, summary],
  );
  const displayCampaigns = useMemo(() => campaigns.map(mapCampaign), [campaigns]);
  const displayMails = useMemo(() => mailMessages.map(mapMail), [mailMessages]);
  const pipelineColumns = useMemo(
    () => buildPipeline(applications),
    [applications],
  );
  const todayItems = useMemo(
    () => buildTodayItems(applications, mailMessages),
    [applications, mailMessages],
  );

  async function refreshAfterAction(successText: string) {
    await loadData();
    setNotice({ type: "success", text: successText });
  }

  async function ensureApplicationDocuments(application: ApplicationDto) {
    const hasCoverLetter = application.documents.some(
      (document) => document.document_type === "cover_letter",
    );
    const hasEmail = application.documents.some(
      (document) => document.document_type === "email",
    );
    if (!hasCoverLetter || !hasEmail) {
      await generateApplicationDocuments(application.id);
    }
    return getApplication(application.id);
  }

  async function handleCreateApplication(job: Job) {
    if (!job.apiId) return;
    setNotice(null);
    setActionState("creating-application");
    try {
      const application = await createApplicationForJob(job.apiId);
      const reviewedApplication = await ensureApplicationDocuments(application);
      setReviewApplication(reviewedApplication);
      await loadData();
      setNotice({ type: "success", text: "Bewerbungsentwürfe wurden erstellt." });
    } catch (error) {
      setNotice({ type: "error", text: readableError(error) });
    } finally {
      setActionState("idle");
    }
  }

  async function handleCreateGmailDraft(job: Job) {
    if (!job.apiId) return;
    setNotice(null);
    setActionState("creating-draft");
    try {
      let application = applications.find((item) => item.job === job.apiId);
      if (!application) {
        application = await createApplicationForJob(job.apiId);
      }

      const approvedEmail = application.documents.find(
        (document) => document.document_type === "email" && document.is_approved,
      );

      if (!approvedEmail) {
        const reviewedApplication = await ensureApplicationDocuments(application);
        setReviewApplication(reviewedApplication);
        setNotice({
          type: "success",
          text: "Bitte prüfe und bestätige zuerst den E-Mail-Entwurf.",
        });
        return;
      }

      await createGmailDraft(application.id);
      await refreshAfterAction("Gmail-Entwurf wurde simuliert erstellt.");
    } catch (error) {
      setNotice({ type: "error", text: readableError(error) });
    } finally {
      setActionState("idle");
    }
  }

  async function handleSaveReviewDocument(
    document: ApplicationDocumentDto,
    payload: Pick<ApplicationDocumentDto, "title" | "content">,
  ) {
    if (!reviewApplication) return;
    setNotice(null);
    try {
      await updateApplicationDocument(reviewApplication.id, document.id, payload);
      const updatedApplication = await getApplication(reviewApplication.id);
      setReviewApplication(updatedApplication);
      await loadData();
      setNotice({ type: "success", text: "Dokument wurde gespeichert." });
    } catch (error) {
      setNotice({ type: "error", text: readableError(error) });
    }
  }

  async function handleApproveReviewDocument(document: ApplicationDocumentDto) {
    if (!reviewApplication) return;
    setNotice(null);
    try {
      await approveApplicationDocument(reviewApplication.id, document.id);
      const updatedApplication = await getApplication(reviewApplication.id);
      setReviewApplication(updatedApplication);
      await loadData();
      setNotice({ type: "success", text: "Entwurf wurde freigegeben." });
    } catch (error) {
      setNotice({ type: "error", text: readableError(error) });
    }
  }

  async function handleCreateReviewGmailDraft() {
    if (!reviewApplication) return;
    setNotice(null);
    setActionState("creating-draft");
    try {
      await createGmailDraft(reviewApplication.id);
      setReviewApplication(null);
      await refreshAfterAction("Gmail-Entwurf wurde simuliert erstellt.");
    } catch (error) {
      setNotice({ type: "error", text: readableError(error) });
    } finally {
      setActionState("idle");
    }
  }

  async function handleSyncMail() {
    setNotice(null);
    setActionState("syncing-mail");
    try {
      await syncMail();
      await refreshAfterAction("Mail-Synchronisierung wurde simuliert.");
    } catch (error) {
      setNotice({ type: "error", text: readableError(error) });
    } finally {
      setActionState("idle");
    }
  }

  async function handleCreateCampaign(form: CampaignFormState) {
    setNotice(null);
    setActionState("creating-campaign");
    try {
      const campaign = await createCampaign({
        name: form.name,
        keywords: splitCsv(form.keywords),
        industries: splitCsv(form.industries),
        sources: form.sources,
        location: form.location,
        radius_km: form.radius_km,
        remote_allowed: form.remote_allowed,
        hybrid_allowed: form.hybrid_allowed,
        exclude_keywords: splitCsv(form.exclude_keywords),
        status: "draft",
      });
      await runCampaign(campaign.id);
      setIsCampaignModalOpen(false);
      await refreshAfterAction("Suchkampagne wurde erstellt und gestartet.");
    } catch (error) {
      setNotice({ type: "error", text: readableError(error) });
    } finally {
      setActionState("idle");
    }
  }

  async function handleCreateManualJob(form: ManualJobFormState) {
    setNotice(null);
    setActionState("importing-job");
    try {
      const createdJob = await createManualJobPosting(manualJobPayload(form));
      setIsManualJobModalOpen(false);
      await loadData();
      setSelectedJobId(createdJob.id);
      setNotice({ type: "success", text: "Stelle wurde hinzugefügt und bewertet." });
    } catch (error) {
      setNotice({ type: "error", text: readableError(error) });
    } finally {
      setActionState("idle");
    }
  }

  return (
    <>
      <div className="mx-auto max-w-[1504px] px-8 py-7">
          <Header
            onOpenCampaignModal={() => setIsCampaignModalOpen(true)}
            onOpenManualJobModal={() => setIsManualJobModalOpen(true)}
          />
          {notice ? <NoticeBanner notice={notice} onDismiss={() => setNotice(null)} /> : null}
          {loadError ? (
            <ErrorState message={loadError} onRetry={loadData} />
          ) : (
            <>
              <section className="mt-6 grid grid-cols-5 gap-4">
                {kpis.map((kpi) => (
                  <KpiCard key={kpi.label} kpi={kpi} loading={isLoading} />
                ))}
              </section>
              <section className="mt-5 grid grid-cols-[1.04fr_0.96fr] gap-4">
                <JobRankingPanel
                  jobs={displayJobs}
                  selectedJobId={selectedJob?.apiId ?? null}
                  loading={isLoading}
                  onSelectJob={setSelectedJobId}
                />
                <JobDetailPanel
                  job={selectedJob}
                  loading={isLoading}
                  actionState={actionState}
                  onCreateApplication={handleCreateApplication}
                  onCreateGmailDraft={handleCreateGmailDraft}
                />
              </section>
              <section className="mt-4 grid grid-cols-[0.92fr_1.03fr_0.92fr] gap-4">
                <CampaignsPanel campaigns={displayCampaigns} loading={isLoading} />
                <MailCenterPanel
                  mails={displayMails}
                  loading={isLoading}
                  syncing={actionState === "syncing-mail"}
                  onSync={handleSyncMail}
                />
                <TodayImportantPanel items={todayItems} loading={isLoading} />
              </section>
              <section className="mt-4">
                <PipelineBoard columns={pipelineColumns} loading={isLoading} />
              </section>
            </>
          )}
      </div>
      {isCampaignModalOpen ? (
        <CampaignModal
          submitting={actionState === "creating-campaign"}
          onClose={() => setIsCampaignModalOpen(false)}
          onSubmit={handleCreateCampaign}
        />
      ) : null}
      {isManualJobModalOpen ? (
        <ManualJobModal
          submitting={actionState === "importing-job"}
          onClose={() => setIsManualJobModalOpen(false)}
          onSubmit={handleCreateManualJob}
        />
      ) : null}
      {reviewApplication ? (
        <ApplicationReviewModal
          application={reviewApplication}
          submitting={actionState === "creating-draft"}
          onClose={() => setReviewApplication(null)}
          onSaveDocument={handleSaveReviewDocument}
          onApproveDocument={handleApproveReviewDocument}
          onCreateGmailDraft={handleCreateReviewGmailDraft}
        />
      ) : null}
    </>
  );
}

function Sidebar() {
  return (
    <aside className="fixed inset-y-0 left-0 z-10 flex w-[292px] flex-col border-r border-slate-200 bg-white">
      <div className="flex h-20 items-center gap-3 px-6">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-600 text-white shadow-sm shadow-blue-200">
          <BriefcaseGlyph />
        </div>
        <div className="text-lg font-bold tracking-[-0.01em]">
          AI Job Application Copilot
        </div>
      </div>
      <nav className="mt-3 flex-1 space-y-2 px-4">
        {navigationItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.label}
              to={item.path}
              end={item.path === "/"}
              className={({ isActive }) =>
                cn(
                  "flex h-12 w-full items-center gap-4 rounded-xl px-4 text-left text-[15px] font-medium transition",
                  isActive
                    ? "bg-blue-50 text-blue-700 shadow-[inset_3px_0_0_#2563eb]"
                    : "text-slate-600 hover:bg-slate-50 hover:text-slate-950",
                )
              }
            >
              <Icon size={19} />
              {item.label}
            </NavLink>
          );
        })}
      </nav>
      <div className="p-4">
        <div className="flex items-center gap-3 rounded-xl border border-slate-200 bg-white p-3 shadow-sm">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-blue-600 text-sm font-bold text-white">
            MB
          </div>
          <div className="min-w-0 flex-1">
            <div className="truncate text-sm font-semibold">Max Beispiel</div>
            <div className="truncate text-xs text-slate-500">
              max.beispiel@gmail.com
            </div>
          </div>
          <ChevronDown size={16} className="text-slate-500" />
        </div>
      </div>
    </aside>
  );
}

function Header({
  onOpenCampaignModal,
  onOpenManualJobModal,
}: {
  onOpenCampaignModal: () => void;
  onOpenManualJobModal: () => void;
}) {
  return (
    <header className="flex items-center justify-between">
      <div className="flex items-center gap-5">
        <h1 className="text-[28px] font-bold tracking-[-0.03em]">
          Bewerber-Dashboard
        </h1>
        <div className="flex items-center gap-2 rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm font-semibold text-emerald-700">
          <GmailMark />
          Gmail verbunden
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
        </div>
      </div>
      <div className="flex items-center gap-3">
        <button
          className="inline-flex h-11 items-center gap-2 rounded-lg border border-slate-200 bg-white px-5 text-sm font-semibold text-slate-800 shadow-sm transition hover:bg-slate-50"
          onClick={onOpenManualJobModal}
        >
          <Plus size={18} />
          Stelle manuell hinzufügen
        </button>
        <button
          className="inline-flex h-11 items-center gap-2 rounded-lg bg-blue-600 px-5 text-sm font-semibold text-white shadow-sm shadow-blue-200 transition hover:bg-blue-700"
          onClick={onOpenCampaignModal}
        >
          <Plus size={18} />
          Neue Suchkampagne
        </button>
      </div>
    </header>
  );
}

function PlaceholderPage({ title }: { title: string }) {
  return (
    <div className="mx-auto max-w-[1504px] px-8 py-7">
      <header className="flex items-center justify-between">
        <h1 className="text-[28px] font-bold tracking-[-0.03em]">{title}</h1>
      </header>
      <section className="card mt-6 p-8">
        <h2 className="text-lg font-bold">Bereich in Vorbereitung</h2>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
          Diese Seite ist als Routing-Ziel angelegt. Die Detailansicht wird in einem
          späteren Schritt umgesetzt; das Dashboard bleibt unter Übersicht verfügbar.
        </p>
      </section>
    </div>
  );
}

function JobsPage() {
  const [jobs, setJobs] = useState<JobPostingDto[]>([]);
  const [applications, setApplications] = useState<ApplicationDto[]>([]);
  const [loading, setLoading] = useState(true);
  const [notice, setNotice] = useState<Notice | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [isManualJobModalOpen, setIsManualJobModalOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const loadJobsPageData = useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    try {
      const [jobsData, applicationsData] = await Promise.all([
        getJobs(),
        getApplications(),
      ]);
      setJobs(jobsData);
      setApplications(applicationsData);
    } catch (error) {
      setLoadError(readableError(error));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadJobsPageData();
  }, [loadJobsPageData]);

  async function handleCreateManualJob(form: ManualJobFormState) {
    setNotice(null);
    setSubmitting(true);
    try {
      await createManualJobPosting(manualJobPayload(form));
      setIsManualJobModalOpen(false);
      await loadJobsPageData();
      setNotice({ type: "success", text: "Stelle wurde hinzugefügt und bewertet." });
    } catch (error) {
      setNotice({ type: "error", text: readableError(error) });
    } finally {
      setSubmitting(false);
    }
  }

  const displayJobs = useMemo(() => jobs.map((job) => mapJob(job, applications)), [
    applications,
    jobs,
  ]);

  return (
    <>
      <div className="mx-auto max-w-[1504px] px-8 py-7">
        <header className="flex items-center justify-between">
          <div>
            <h1 className="text-[28px] font-bold tracking-[-0.03em]">
              Gefundene Jobs
            </h1>
            <p className="mt-1 text-sm font-medium text-slate-500">
              Manuell importierte und mock-basiert gefundene Stellen.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <NavLink
              className="inline-flex h-11 items-center gap-2 rounded-lg border border-slate-200 bg-white px-5 text-sm font-semibold text-slate-800 shadow-sm transition hover:bg-slate-50"
              to="/"
            >
              Zur Übersicht
            </NavLink>
            <button
              className="inline-flex h-11 items-center gap-2 rounded-lg bg-blue-600 px-5 text-sm font-semibold text-white shadow-sm shadow-blue-200 transition hover:bg-blue-700"
              onClick={() => setIsManualJobModalOpen(true)}
            >
              <Plus size={18} />
              Stelle manuell hinzufügen
            </button>
          </div>
        </header>
        {notice ? <NoticeBanner notice={notice} onDismiss={() => setNotice(null)} /> : null}
        {loadError ? (
          <ErrorState message={loadError} onRetry={loadJobsPageData} />
        ) : (
          <section className="card mt-6 overflow-hidden">
            <PanelHeader title="Jobliste" />
            <div className="divide-y divide-slate-100">
              {loading ? (
                <SkeletonRows count={5} />
              ) : displayJobs.length ? (
                displayJobs.map((job) => (
                  <div
                    key={job.id}
                    className="grid grid-cols-[1fr_88px_150px_140px_130px] items-center gap-4 px-5 py-4"
                  >
                    <div className="min-w-0">
                      <div className="truncate text-sm font-bold text-slate-900">
                        {job.title}
                      </div>
                      <div className="mt-1 truncate text-sm text-slate-500">
                        {job.company} · {job.location} · {job.mode}
                      </div>
                    </div>
                    <ScoreBadge score={job.score} compact />
                    <StatusBadge label={job.status} tone={job.statusTone} />
                    <div className="truncate text-sm font-semibold text-slate-600">
                      {jobs.find((item) => item.id === job.apiId)?.source || "Manuell"}
                    </div>
                    <NavLink
                      className="inline-flex h-9 items-center justify-center rounded-lg border border-slate-200 bg-white px-3 text-sm font-semibold text-blue-700 hover:bg-blue-50"
                      to="/"
                    >
                      Dashboard
                    </NavLink>
                  </div>
                ))
              ) : (
                <EmptyState text="Noch keine Jobs vorhanden." />
              )}
            </div>
          </section>
        )}
      </div>
      {isManualJobModalOpen ? (
        <ManualJobModal
          submitting={submitting}
          onClose={() => setIsManualJobModalOpen(false)}
          onSubmit={handleCreateManualJob}
        />
      ) : null}
    </>
  );
}

function ApplicationsPage() {
  const navigate = useNavigate();
  const [applications, setApplications] = useState<ApplicationDto[]>([]);
  const [activeFilter, setActiveFilter] = useState<ApplicationFilterKey>("all");
  const [loading, setLoading] = useState(true);
  const [notice, setNotice] = useState<Notice | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [busyApplicationId, setBusyApplicationId] = useState<number | null>(null);

  const loadApplicationsPageData = useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    try {
      setApplications(await getApplications());
    } catch (error) {
      setLoadError(readableError(error));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadApplicationsPageData();
  }, [loadApplicationsPageData]);

  const filteredApplications = useMemo(() => {
    const filter = applicationFilters.find((item) => item.key === activeFilter);
    if (!filter || filter.key === "all") return applications;
    return applications.filter((application) => filter.statuses.includes(application.status));
  }, [activeFilter, applications]);

  async function handlePatchApplication(
    applicationId: number,
    payload: UpdateApplicationPayload,
    successText: string,
  ) {
    setNotice(null);
    setBusyApplicationId(applicationId);
    try {
      await updateApplication(applicationId, payload);
      await loadApplicationsPageData();
      setNotice({ type: "success", text: successText });
    } catch (error) {
      setNotice({ type: "error", text: readableError(error) });
    } finally {
      setBusyApplicationId(null);
    }
  }

  async function handleMarkApplied(applicationId: number) {
    setNotice(null);
    setBusyApplicationId(applicationId);
    try {
      await markApplicationApplied(applicationId);
      await loadApplicationsPageData();
      setNotice({ type: "success", text: "Bewerbung wurde als beworben markiert." });
    } catch (error) {
      setNotice({ type: "error", text: readableError(error) });
    } finally {
      setBusyApplicationId(null);
    }
  }

  async function handleCreateDraft(application: ApplicationDto) {
    setNotice(null);
    setBusyApplicationId(application.id);
    try {
      await createGmailDraft(application.id);
      await loadApplicationsPageData();
      setNotice({ type: "success", text: "Gmail-Entwurf wurde simuliert erstellt." });
    } catch (error) {
      setNotice({ type: "error", text: readableError(error) });
    } finally {
      setBusyApplicationId(null);
    }
  }

  return (
    <div className="mx-auto max-w-[1504px] px-8 py-7">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-[28px] font-bold tracking-[-0.03em]">Bewerbungen</h1>
          <p className="mt-1 text-sm font-medium text-slate-500">
            Bewerbungen prüfen, Status pflegen und Follow-ups planen.
          </p>
        </div>
        <NavLink
          className="inline-flex h-11 items-center gap-2 rounded-lg border border-slate-200 bg-white px-5 text-sm font-semibold text-slate-800 shadow-sm transition hover:bg-slate-50"
          to="/"
        >
          Zur Übersicht
        </NavLink>
      </header>
      {notice ? <NoticeBanner notice={notice} onDismiss={() => setNotice(null)} /> : null}
      {loadError ? (
        <ErrorState message={loadError} onRetry={loadApplicationsPageData} />
      ) : (
        <>
          <section className="card mt-6 p-4">
            <div className="flex flex-wrap gap-2">
              {applicationFilters.map((filter) => (
                <button
                  key={filter.key}
                  className={cn(
                    "rounded-lg border px-3 py-2 text-sm font-bold transition",
                    activeFilter === filter.key
                      ? "border-blue-200 bg-blue-50 text-blue-700"
                      : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50",
                  )}
                  onClick={() => setActiveFilter(filter.key)}
                >
                  {filter.label}
                </button>
              ))}
            </div>
          </section>
          <section className="mt-4 space-y-3">
            {loading ? (
              <section className="card p-4">
                <SkeletonRows count={5} />
              </section>
            ) : filteredApplications.length ? (
              filteredApplications.map((application) => (
                <ApplicationListCard
                  key={application.id}
                  application={application}
                  busy={busyApplicationId === application.id}
                  onOpen={() => navigate(`/bewerbungen/${application.id}`)}
                  onCreateDraft={() => handleCreateDraft(application)}
                  onMarkApplied={() => handleMarkApplied(application.id)}
                  onSetFollowUp={(value) =>
                    handlePatchApplication(
                      application.id,
                      { follow_up_at: dateInputToDateTime(value) },
                      "Follow-up-Datum wurde gespeichert.",
                    )
                  }
                  onClose={() =>
                    handlePatchApplication(
                      application.id,
                      { status: "closed" },
                      "Bewerbung wurde abgeschlossen.",
                    )
                  }
                />
              ))
            ) : (
              <section className="card p-8">
                <EmptyState text="Keine Bewerbungen für diesen Filter gefunden." />
              </section>
            )}
          </section>
        </>
      )}
    </div>
  );
}

function ApplicationListCard({
  application,
  busy,
  onOpen,
  onCreateDraft,
  onMarkApplied,
  onSetFollowUp,
  onClose,
}: {
  application: ApplicationDto;
  busy: boolean;
  onOpen: () => void;
  onCreateDraft: () => void;
  onMarkApplied: () => void;
  onSetFollowUp: (value: string) => void;
  onClose: () => void;
}) {
  const [followUpDate, setFollowUpDate] = useState(dateInputValue(application.follow_up_at));
  const due = isFollowUpDue(application.follow_up_at);

  useEffect(() => {
    setFollowUpDate(dateInputValue(application.follow_up_at));
  }, [application.follow_up_at]);

  function stopAndRun(event: MouseEvent, action: () => void) {
    event.stopPropagation();
    action();
  }

  return (
    <article
      className="card cursor-pointer p-5 transition hover:border-blue-200 hover:shadow-md"
      onClick={onOpen}
    >
      <div className="grid grid-cols-[1fr_88px_168px] items-start gap-5">
        <div className="min-w-0">
          <div className="text-sm font-semibold text-slate-500">
            {application.job_detail.company}
          </div>
          <h2 className="mt-1 truncate text-lg font-bold tracking-[-0.02em]">
            {application.job_detail.title}
          </h2>
          <div className="mt-2 flex flex-wrap items-center gap-2 text-sm text-slate-500">
            <span>{application.job_detail.location || "Standort offen"}</span>
            <span>·</span>
            <span>{remoteTypeLabel(application.job_detail.remote_type)}</span>
            <span>·</span>
            <span>Aktualisiert {relativeDate(application.updated_at)}</span>
          </div>
        </div>
        <ScoreBadge score={application.match_score ?? 0} compact />
        <StatusBadge
          label={applicationStatusLabel(application.status)}
          tone={applicationStatusTone(application.status)}
        />
      </div>
      <div className="mt-4 grid grid-cols-4 gap-3">
        <ApplicationMeta label="Beworben am" value={formatNullableDate(application.applied_at)} />
        <ApplicationMeta
          label="Follow-up"
          value={formatNullableDate(application.follow_up_at)}
          due={due}
        />
        <ApplicationMeta label="Erstellt" value={formatNullableDate(application.created_at)} />
        <ApplicationMeta label="Dokumente" value={`${application.documents.length}`} />
      </div>
      <div className="mt-4 flex flex-wrap items-end gap-2 border-t border-slate-100 pt-4">
        <NavLink
          className="inline-flex h-9 items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 text-sm font-semibold text-blue-700 hover:bg-blue-50"
          to={`/bewerbungen/${application.id}`}
          onClick={(event) => event.stopPropagation()}
        >
          <FileText size={15} />
          Dokumente prüfen
        </NavLink>
        <button
          className="inline-flex h-9 items-center gap-2 rounded-lg bg-blue-600 px-3 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-60"
          disabled={busy}
          onClick={(event) => stopAndRun(event, onCreateDraft)}
        >
          {busy ? <Loader2 size={15} className="animate-spin" /> : <MailIcon size={15} />}
          Gmail-Entwurf erstellen
        </button>
        <button
          className="inline-flex h-9 items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 text-sm font-semibold text-slate-800 hover:bg-slate-50 disabled:opacity-60"
          disabled={busy || application.status === "applied"}
          onClick={(event) => stopAndRun(event, onMarkApplied)}
        >
          <Send size={15} />
          Als beworben markieren
        </button>
        <label
          className={cn(
            "flex h-9 items-center gap-2 rounded-lg border px-3 text-sm font-semibold",
            due
              ? "border-orange-200 bg-orange-50 text-orange-800"
              : "border-slate-200 bg-white text-slate-700",
          )}
          onClick={(event) => event.stopPropagation()}
        >
          Follow-up-Datum setzen
          <input
            className="h-7 rounded-md border border-slate-200 px-2 text-sm outline-none"
            type="date"
            value={followUpDate}
            onChange={(event) => setFollowUpDate(event.target.value)}
          />
        </label>
        <button
          className="h-9 rounded-lg border border-slate-200 bg-white px-3 text-sm font-semibold text-slate-800 hover:bg-slate-50 disabled:opacity-60"
          disabled={busy || followUpDate === dateInputValue(application.follow_up_at)}
          onClick={(event) => stopAndRun(event, () => onSetFollowUp(followUpDate))}
        >
          Speichern
        </button>
        <button
          className="h-9 rounded-lg border border-slate-200 bg-white px-3 text-sm font-semibold text-slate-800 hover:bg-slate-50 disabled:opacity-60"
          disabled={busy || application.status === "closed"}
          onClick={(event) => stopAndRun(event, onClose)}
        >
          Als abgeschlossen markieren
        </button>
      </div>
    </article>
  );
}

function ApplicationMeta({
  label,
  value,
  due = false,
}: {
  label: string;
  value: string;
  due?: boolean;
}) {
  return (
    <div
      className={cn(
        "rounded-lg border px-3 py-2",
        due ? "border-orange-200 bg-orange-50" : "border-slate-100 bg-slate-50",
      )}
    >
      <div className="text-[11px] font-bold uppercase text-slate-500">{label}</div>
      <div className={cn("mt-1 text-sm font-bold", due ? "text-orange-800" : "text-slate-800")}>
        {value}
      </div>
    </div>
  );
}

function MailPage() {
  const [messages, setMessages] = useState<EmailMessageDto[]>([]);
  const [applications, setApplications] = useState<ApplicationDto[]>([]);
  const [activeFilter, setActiveFilter] = useState<MailFilterKey>("all");
  const [selectedMessageId, setSelectedMessageId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [notice, setNotice] = useState<Notice | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [busyMessageId, setBusyMessageId] = useState<number | null>(null);
  const [syncing, setSyncing] = useState(false);

  const loadMailPageData = useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    try {
      const [mailData, applicationData] = await Promise.all([
        getMailMessages(),
        getApplications(),
      ]);
      setMessages(mailData);
      setApplications(applicationData);
    } catch (error) {
      setLoadError(readableError(error));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadMailPageData();
  }, [loadMailPageData]);

  const filteredMessages = useMemo(() => {
    const filter = mailFilters.find((item) => item.key === activeFilter) ?? mailFilters[0];
    return messages.filter(filter.predicate);
  }, [activeFilter, messages]);
  const selectedMessage =
    messages.find((message) => message.id === selectedMessageId) ?? null;

  async function handleSync() {
    setNotice(null);
    setSyncing(true);
    try {
      await syncMail();
      await loadMailPageData();
      setNotice({ type: "success", text: "Mail-Synchronisierung wurde simuliert." });
    } catch (error) {
      setNotice({ type: "error", text: readableError(error) });
    } finally {
      setSyncing(false);
    }
  }

  async function handleClassify(messageId: number) {
    setNotice(null);
    setBusyMessageId(messageId);
    try {
      await classifyMailMessage(messageId);
      await loadMailPageData();
      setNotice({ type: "success", text: "E-Mail wurde neu klassifiziert." });
    } catch (error) {
      setNotice({ type: "error", text: readableError(error) });
    } finally {
      setBusyMessageId(null);
    }
  }

  async function handleLinkMessage(messageId: number, applicationId: number | null) {
    setNotice(null);
    setBusyMessageId(messageId);
    try {
      await updateMailMessage(messageId, { application: applicationId });
      await loadMailPageData();
      setNotice({ type: "success", text: "E-Mail wurde der Bewerbung zugeordnet." });
    } catch (error) {
      setNotice({ type: "error", text: readableError(error) });
    } finally {
      setBusyMessageId(null);
    }
  }

  async function handleUpdateLinkedApplicationStatus(message: EmailMessageDto) {
    if (!message.application) return;
    const status = suggestedApplicationStatus(message.classification);
    if (!status) return;
    setNotice(null);
    setBusyMessageId(message.id);
    try {
      await updateApplication(message.application, { status });
      await loadMailPageData();
      setNotice({ type: "success", text: "Bewerbungsstatus wurde aktualisiert." });
    } catch (error) {
      setNotice({ type: "error", text: readableError(error) });
    } finally {
      setBusyMessageId(null);
    }
  }

  function handleReplyDraftPlaceholder() {
    setNotice({
      type: "success",
      text: "Antwortentwürfe werden in einem späteren Schritt umgesetzt.",
    });
  }

  return (
    <div className="mx-auto max-w-[1504px] px-8 py-7">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-[28px] font-bold tracking-[-0.03em]">Mail-Zentrale</h1>
          <p className="mt-1 text-sm font-medium text-slate-500">
            Simulierte Antworten prüfen, klassifizieren und Bewerbungen zuordnen.
          </p>
        </div>
        <button
          className="inline-flex h-11 items-center gap-2 rounded-lg bg-blue-600 px-5 text-sm font-semibold text-white shadow-sm shadow-blue-200 transition hover:bg-blue-700 disabled:opacity-70"
          disabled={syncing}
          onClick={handleSync}
        >
          <RefreshCw size={18} className={syncing ? "animate-spin" : ""} />
          Synchronisieren
        </button>
      </header>
      {notice ? <NoticeBanner notice={notice} onDismiss={() => setNotice(null)} /> : null}
      {loadError ? (
        <ErrorState message={loadError} onRetry={loadMailPageData} />
      ) : (
        <>
          <section className="card mt-6 p-4">
            <div className="flex flex-wrap gap-2">
              {mailFilters.map((filter) => (
                <button
                  key={filter.key}
                  className={cn(
                    "rounded-lg border px-3 py-2 text-sm font-bold transition",
                    activeFilter === filter.key
                      ? "border-blue-200 bg-blue-50 text-blue-700"
                      : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50",
                  )}
                  onClick={() => setActiveFilter(filter.key)}
                >
                  {filter.label}
                </button>
              ))}
            </div>
          </section>
          <section className="mt-4 space-y-3">
            {loading ? (
              <section className="card p-4">
                <SkeletonRows count={5} />
              </section>
            ) : filteredMessages.length ? (
              filteredMessages.map((message) => (
                <MailListCard
                  key={message.id}
                  message={message}
                  busy={busyMessageId === message.id}
                  onOpen={() => setSelectedMessageId(message.id)}
                  onClassify={() => handleClassify(message.id)}
                  onReplyDraft={handleReplyDraftPlaceholder}
                />
              ))
            ) : (
              <section className="card p-8">
                <EmptyState text="Keine E-Mails für diesen Filter gefunden." />
              </section>
            )}
          </section>
        </>
      )}
      {selectedMessage ? (
        <MailDetailModal
          message={selectedMessage}
          applications={applications}
          busy={busyMessageId === selectedMessage.id}
          onClose={() => setSelectedMessageId(null)}
          onClassify={() => handleClassify(selectedMessage.id)}
          onLink={(applicationId) => handleLinkMessage(selectedMessage.id, applicationId)}
          onUpdateApplicationStatus={() =>
            handleUpdateLinkedApplicationStatus(selectedMessage)
          }
          onReplyDraft={handleReplyDraftPlaceholder}
        />
      ) : null}
    </div>
  );
}

function MailListCard({
  message,
  busy,
  onOpen,
  onClassify,
  onReplyDraft,
}: {
  message: EmailMessageDto;
  busy: boolean;
  onOpen: () => void;
  onClassify: () => void;
  onReplyDraft: () => void;
}) {
  function stopAndRun(event: MouseEvent, action: () => void) {
    event.stopPropagation();
    action();
  }

  return (
    <article
      className="card cursor-pointer p-5 transition hover:border-blue-200 hover:shadow-md"
      onClick={onOpen}
    >
      <div className="grid grid-cols-[1fr_auto] gap-4">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h2 className="truncate text-base font-bold tracking-[-0.02em]">
              {message.subject}
            </h2>
            <StatusBadge
              label={classificationLabel(message.classification)}
              tone={classificationTone(message.classification)}
            />
            {message.requires_action ? (
              <span className="rounded-md border border-orange-200 bg-orange-50 px-2 py-0.5 text-xs font-bold text-orange-800">
                Aktion erforderlich
              </span>
            ) : null}
          </div>
          <div className="mt-2 text-sm font-semibold text-slate-600">
            {displaySender(message.sender)}
          </div>
          <p className="mt-2 line-clamp-2 text-sm leading-6 text-slate-500">
            {message.body}
          </p>
        </div>
        <div className="text-right text-sm font-semibold text-slate-500">
          {formatNullableDate(message.received_at)}
        </div>
      </div>
      <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 pt-4">
        <div className="min-w-0 text-sm text-slate-500">
          {message.application_summary ? (
            <span>
              Zugeordnet:{" "}
              <strong className="text-slate-800">
                {message.application_summary.company} – {message.application_summary.title}
              </strong>
            </span>
          ) : (
            <span>Nicht zugeordnet</span>
          )}
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            className="inline-flex h-9 items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 text-sm font-semibold text-slate-800 hover:bg-slate-50 disabled:opacity-60"
            disabled={busy}
            onClick={(event) => stopAndRun(event, onClassify)}
          >
            {busy ? <Loader2 size={15} className="animate-spin" /> : <RefreshCw size={15} />}
            Neu klassifizieren
          </button>
          {canCreateReplyDraft(message.classification) ? (
            <button
              className="inline-flex h-9 items-center gap-2 rounded-lg bg-blue-600 px-3 text-sm font-semibold text-white hover:bg-blue-700"
              onClick={(event) => stopAndRun(event, onReplyDraft)}
            >
              <PenLine size={15} />
              Antwortentwurf erstellen
            </button>
          ) : null}
        </div>
      </div>
    </article>
  );
}

function MailDetailModal({
  message,
  applications,
  busy,
  onClose,
  onClassify,
  onLink,
  onUpdateApplicationStatus,
  onReplyDraft,
}: {
  message: EmailMessageDto;
  applications: ApplicationDto[];
  busy: boolean;
  onClose: () => void;
  onClassify: () => void;
  onLink: (applicationId: number | null) => void;
  onUpdateApplicationStatus: () => void;
  onReplyDraft: () => void;
}) {
  const suggestedStatus = suggestedApplicationStatus(message.classification);

  return (
    <div className="fixed inset-0 z-20 flex items-center justify-center bg-slate-950/35 px-4 py-8">
      <div className="max-h-[92vh] w-full max-w-4xl overflow-auto rounded-2xl border border-slate-200 bg-white p-6 shadow-2xl">
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <div className="text-sm font-semibold text-slate-500">
              {displaySender(message.sender)}
            </div>
            <h2 className="mt-1 text-xl font-bold tracking-[-0.02em]">
              {message.subject}
            </h2>
            <div className="mt-3 flex flex-wrap items-center gap-2">
              <StatusBadge
                label={classificationLabel(message.classification)}
                tone={classificationTone(message.classification)}
              />
              {message.requires_action ? (
                <span className="rounded-md border border-orange-200 bg-orange-50 px-2 py-0.5 text-xs font-bold text-orange-800">
                  Aktion erforderlich
                </span>
              ) : null}
              <span className="text-sm font-semibold text-slate-500">
                Eingang: {formatNullableDate(message.received_at)}
              </span>
            </div>
          </div>
          <button
            type="button"
            className="rounded-lg p-2 text-slate-500 hover:bg-slate-100"
            onClick={onClose}
          >
            <X size={20} />
          </button>
        </div>

        <div className="mt-6 grid grid-cols-[1fr_320px] gap-4">
          <div className="rounded-xl border border-slate-100 bg-slate-50 p-4">
            <h3 className="text-sm font-bold">Nachricht</h3>
            <p className="mt-3 whitespace-pre-wrap text-sm leading-7 text-slate-700">
              {message.body}
            </p>
          </div>
          <div className="space-y-4">
            <div className="rounded-xl border border-slate-100 bg-white p-4">
              <h3 className="text-sm font-bold">Bewerbung zuordnen</h3>
              <select
                className="mt-3 h-10 w-full rounded-lg border border-slate-200 bg-white px-3 text-sm outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
                value={message.application ?? ""}
                onChange={(event) =>
                  onLink(event.target.value ? Number(event.target.value) : null)
                }
              >
                <option value="">Keine Zuordnung</option>
                {applications.map((application) => (
                  <option key={application.id} value={application.id}>
                    {application.job_detail.company} – {application.job_detail.title}
                  </option>
                ))}
              </select>
              {message.application_summary ? (
                <div className="mt-3 rounded-lg border border-blue-100 bg-blue-50 px-3 py-2 text-sm font-semibold text-blue-800">
                  {message.application_summary.company} –{" "}
                  {message.application_summary.title}
                </div>
              ) : null}
            </div>

            <div className="rounded-xl border border-slate-100 bg-white p-4">
              <h3 className="text-sm font-bold">Vorschlag</h3>
              <p className="mt-2 text-sm leading-6 text-slate-600">
                {suggestedMailAction(message.classification)}
              </p>
              {message.application && suggestedStatus ? (
                <button
                  className="mt-3 inline-flex h-10 w-full items-center justify-center gap-2 rounded-lg bg-blue-600 px-3 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-60"
                  disabled={busy}
                  onClick={onUpdateApplicationStatus}
                >
                  {busy ? <Loader2 size={15} className="animate-spin" /> : <Check size={15} />}
                  Status aktualisieren
                </button>
              ) : (
                <p className="mt-3 rounded-lg border border-slate-100 bg-slate-50 px-3 py-2 text-xs font-semibold text-slate-500">
                  Für Statusaktionen zuerst eine Bewerbung zuordnen.
                </p>
              )}
            </div>

            <div className="rounded-xl border border-slate-100 bg-white p-4">
              <h3 className="text-sm font-bold">Aktionen</h3>
              <div className="mt-3 space-y-2">
                <button
                  className="inline-flex h-10 w-full items-center justify-center gap-2 rounded-lg border border-slate-200 bg-white px-3 text-sm font-semibold text-slate-800 hover:bg-slate-50 disabled:opacity-60"
                  disabled={busy}
                  onClick={onClassify}
                >
                  {busy ? <Loader2 size={15} className="animate-spin" /> : <RefreshCw size={15} />}
                  Neu klassifizieren
                </button>
                {canCreateReplyDraft(message.classification) ? (
                  <button
                    className="inline-flex h-10 w-full items-center justify-center gap-2 rounded-lg bg-blue-600 px-3 text-sm font-semibold text-white hover:bg-blue-700"
                    onClick={onReplyDraft}
                  >
                    <PenLine size={15} />
                    Antwortentwurf erstellen
                  </button>
                ) : null}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function FollowUpsPage() {
  const [applications, setApplications] = useState<ApplicationDto[]>([]);
  const [mailMessages, setMailMessages] = useState<EmailMessageDto[]>([]);
  const [activeFilter, setActiveFilter] = useState<FollowUpFilterKey>("all");
  const [reviewApplication, setReviewApplication] = useState<ApplicationDto | null>(null);
  const [loading, setLoading] = useState(true);
  const [notice, setNotice] = useState<Notice | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [busyApplicationId, setBusyApplicationId] = useState<number | null>(null);

  const loadFollowUpData = useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    try {
      const [applicationData, mailData] = await Promise.all([
        getApplications(),
        getMailMessages(),
      ]);
      setApplications(applicationData);
      setMailMessages(mailData);
    } catch (error) {
      setLoadError(readableError(error));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadFollowUpData();
  }, [loadFollowUpData]);

  const followUpApplications = useMemo(
    () =>
      applications.filter((application) =>
        isFollowUpRelevant(application, mailMessages),
      ),
    [applications, mailMessages],
  );
  const filteredApplications = useMemo(
    () =>
      followUpApplications.filter((application) =>
        matchesFollowUpFilter(application, activeFilter, mailMessages),
      ),
    [activeFilter, followUpApplications, mailMessages],
  );

  async function handlePatchApplication(
    applicationId: number,
    payload: UpdateApplicationPayload,
    successText: string,
  ) {
    setNotice(null);
    setBusyApplicationId(applicationId);
    try {
      await updateApplication(applicationId, payload);
      await loadFollowUpData();
      setNotice({ type: "success", text: successText });
    } catch (error) {
      setNotice({ type: "error", text: readableError(error) });
    } finally {
      setBusyApplicationId(null);
    }
  }

  async function handleGenerateFollowUp(application: ApplicationDto) {
    setNotice(null);
    setBusyApplicationId(application.id);
    try {
      await generateFollowUpDocument(application.id);
      const updatedApplication = await getApplication(application.id);
      setReviewApplication(updatedApplication);
      await loadFollowUpData();
      setNotice({ type: "success", text: "Follow-up-Entwurf wurde erstellt." });
    } catch (error) {
      setNotice({ type: "error", text: readableError(error) });
    } finally {
      setBusyApplicationId(null);
    }
  }

  async function handleSaveFollowUpDocument(
    document: ApplicationDocumentDto,
    payload: Pick<ApplicationDocumentDto, "title" | "content">,
  ) {
    if (!reviewApplication) return;
    setNotice(null);
    try {
      await updateApplicationDocument(reviewApplication.id, document.id, payload);
      const updatedApplication = await getApplication(reviewApplication.id);
      setReviewApplication(updatedApplication);
      await loadFollowUpData();
      setNotice({ type: "success", text: "Follow-up-Entwurf wurde gespeichert." });
    } catch (error) {
      setNotice({ type: "error", text: readableError(error) });
    }
  }

  async function handleApproveFollowUpDocument(document: ApplicationDocumentDto) {
    if (!reviewApplication) return;
    setNotice(null);
    try {
      await approveApplicationDocument(reviewApplication.id, document.id);
      const updatedApplication = await getApplication(reviewApplication.id);
      setReviewApplication(updatedApplication);
      await loadFollowUpData();
      setNotice({ type: "success", text: "Follow-up-Entwurf wurde freigegeben." });
    } catch (error) {
      setNotice({ type: "error", text: readableError(error) });
    }
  }

  async function handleFollowUpDone(application: ApplicationDto) {
    const nextFollowUp = new Date();
    nextFollowUp.setDate(nextFollowUp.getDate() + 14);
    await handlePatchApplication(
      application.id,
      {
        status: "applied",
        follow_up_at: nextFollowUp.toISOString(),
      },
      "Follow-up wurde als erledigt markiert.",
    );
  }

  return (
    <div className="mx-auto max-w-[1504px] px-8 py-7">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-[28px] font-bold tracking-[-0.03em]">Follow-ups</h1>
          <p className="mt-1 text-sm font-medium text-slate-500">
            Fällige Bewerbungs-Follow-ups planen, formulieren und abschließen.
          </p>
        </div>
        <NavLink
          className="inline-flex h-11 items-center gap-2 rounded-lg border border-slate-200 bg-white px-5 text-sm font-semibold text-slate-800 shadow-sm transition hover:bg-slate-50"
          to="/bewerbungen"
        >
          Bewerbungen öffnen
        </NavLink>
      </header>
      {notice ? <NoticeBanner notice={notice} onDismiss={() => setNotice(null)} /> : null}
      {loadError ? (
        <ErrorState message={loadError} onRetry={loadFollowUpData} />
      ) : (
        <>
          <section className="card mt-6 p-4">
            <div className="flex flex-wrap gap-2">
              {followUpFilters.map((filter) => (
                <button
                  key={filter.key}
                  className={cn(
                    "rounded-lg border px-3 py-2 text-sm font-bold transition",
                    activeFilter === filter.key
                      ? "border-blue-200 bg-blue-50 text-blue-700"
                      : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50",
                  )}
                  onClick={() => setActiveFilter(filter.key)}
                >
                  {filter.label}
                </button>
              ))}
            </div>
          </section>
          <section className="mt-4 space-y-3">
            {loading ? (
              <section className="card p-4">
                <SkeletonRows count={5} />
              </section>
            ) : filteredApplications.length ? (
              filteredApplications.map((application) => (
                <FollowUpCard
                  key={application.id}
                  application={application}
                  latestMail={latestMailForApplication(application.id, mailMessages)}
                  busy={busyApplicationId === application.id}
                  onSetFollowUp={(value) =>
                    handlePatchApplication(
                      application.id,
                      { follow_up_at: dateInputToDateTime(value) },
                      "Follow-up-Datum wurde gespeichert.",
                    )
                  }
                  onGenerateDraft={() => handleGenerateFollowUp(application)}
                  onReviewDraft={() => setReviewApplication(application)}
                  onDone={() => handleFollowUpDone(application)}
                />
              ))
            ) : (
              <section className="card p-8">
                <EmptyState text="Keine Follow-ups für diesen Filter gefunden." />
              </section>
            )}
          </section>
        </>
      )}
      {reviewApplication ? (
        <FollowUpReviewModal
          application={reviewApplication}
          onClose={() => setReviewApplication(null)}
          onSaveDocument={handleSaveFollowUpDocument}
          onApproveDocument={handleApproveFollowUpDocument}
        />
      ) : null}
    </div>
  );
}

function FollowUpCard({
  application,
  latestMail,
  busy,
  onSetFollowUp,
  onGenerateDraft,
  onReviewDraft,
  onDone,
}: {
  application: ApplicationDto;
  latestMail: EmailMessageDto | null;
  busy: boolean;
  onSetFollowUp: (value: string) => void;
  onGenerateDraft: () => void;
  onReviewDraft: () => void;
  onDone: () => void;
}) {
  const [followUpDate, setFollowUpDate] = useState(dateInputValue(application.follow_up_at));
  const due = isApplicationFollowUpDue(application, latestMail);
  const followUpDocument = latestDocumentOfType(application, "follow_up");

  useEffect(() => {
    setFollowUpDate(dateInputValue(application.follow_up_at));
  }, [application.follow_up_at]);

  function stopAndRun(event: MouseEvent, action: () => void) {
    event.stopPropagation();
    action();
  }

  return (
    <article className="card p-5">
      <div className="grid grid-cols-[1fr_88px_168px] items-start gap-5">
        <div className="min-w-0">
          <div className="text-sm font-semibold text-slate-500">
            {application.job_detail.company}
          </div>
          <h2 className="mt-1 truncate text-lg font-bold tracking-[-0.02em]">
            {application.job_detail.title}
          </h2>
          <div className="mt-2 flex flex-wrap items-center gap-2 text-sm text-slate-500">
            <span>{application.job_detail.location || "Standort offen"}</span>
            <span>·</span>
            <span>Seit Bewerbung: {daysSinceDate(application.applied_at)}</span>
            {latestMail ? (
              <>
                <span>·</span>
                <span>Letzte Mail: {classificationLabel(latestMail.classification)}</span>
              </>
            ) : null}
          </div>
        </div>
        <ScoreBadge score={application.match_score ?? 0} compact />
        <StatusBadge
          label={applicationStatusLabel(application.status)}
          tone={applicationStatusTone(application.status)}
        />
      </div>
      <div className="mt-4 grid grid-cols-4 gap-3">
        <ApplicationMeta label="Beworben am" value={formatNullableDate(application.applied_at)} />
        <ApplicationMeta
          label="Follow-up"
          value={formatNullableDate(application.follow_up_at)}
          due={due}
        />
        <ApplicationMeta
          label="Entwurf"
          value={followUpDocument ? `Version ${followUpDocument.version}` : "Nicht erstellt"}
        />
        <ApplicationMeta
          label="Mail-Status"
          value={latestMail ? classificationLabel(latestMail.classification) : "Keine Mail"}
        />
      </div>
      <div className="mt-4 flex flex-wrap items-end gap-2 border-t border-slate-100 pt-4">
        <label
          className={cn(
            "flex h-9 items-center gap-2 rounded-lg border px-3 text-sm font-semibold",
            due
              ? "border-orange-200 bg-orange-50 text-orange-800"
              : "border-slate-200 bg-white text-slate-700",
          )}
        >
          Follow-up-Datum setzen
          <input
            className="h-7 rounded-md border border-slate-200 px-2 text-sm outline-none"
            type="date"
            value={followUpDate}
            onChange={(event) => setFollowUpDate(event.target.value)}
          />
        </label>
        <button
          className="h-9 rounded-lg border border-slate-200 bg-white px-3 text-sm font-semibold text-slate-800 hover:bg-slate-50 disabled:opacity-60"
          disabled={busy || followUpDate === dateInputValue(application.follow_up_at)}
          onClick={(event) => stopAndRun(event, () => onSetFollowUp(followUpDate))}
        >
          Speichern
        </button>
        <button
          className="inline-flex h-9 items-center gap-2 rounded-lg bg-blue-600 px-3 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-60"
          disabled={busy}
          onClick={(event) => stopAndRun(event, onGenerateDraft)}
        >
          {busy ? <Loader2 size={15} className="animate-spin" /> : <PenLine size={15} />}
          Follow-up-Entwurf erstellen
        </button>
        <button
          className="h-9 rounded-lg border border-slate-200 bg-white px-3 text-sm font-semibold text-blue-700 hover:bg-blue-50 disabled:opacity-60"
          disabled={!followUpDocument}
          onClick={(event) => stopAndRun(event, onReviewDraft)}
        >
          Entwurf prüfen
        </button>
        <button
          className="h-9 rounded-lg border border-slate-200 bg-white px-3 text-sm font-semibold text-slate-800 hover:bg-slate-50 disabled:opacity-60"
          disabled={busy}
          onClick={(event) => stopAndRun(event, onDone)}
        >
          Follow-up erledigt
        </button>
        <NavLink
          className="inline-flex h-9 items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 text-sm font-semibold text-slate-800 hover:bg-slate-50"
          to={`/bewerbungen/${application.id}`}
        >
          Bewerbung öffnen
        </NavLink>
      </div>
    </article>
  );
}

function FollowUpReviewModal({
  application,
  onClose,
  onSaveDocument,
  onApproveDocument,
}: {
  application: ApplicationDto;
  onClose: () => void;
  onSaveDocument: (
    document: ApplicationDocumentDto,
    payload: Pick<ApplicationDocumentDto, "title" | "content">,
  ) => void;
  onApproveDocument: (document: ApplicationDocumentDto) => void;
}) {
  const document = latestDocumentOfType(application, "follow_up");

  return (
    <div className="fixed inset-0 z-20 flex items-center justify-center bg-slate-950/35 px-4 py-8">
      <div className="max-h-[92vh] w-full max-w-4xl overflow-auto rounded-2xl border border-slate-200 bg-white p-6 shadow-2xl">
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="text-sm font-semibold text-slate-500">
              {application.job_detail.company}
            </div>
            <h2 className="mt-1 text-xl font-bold tracking-[-0.02em]">
              Follow-up-Entwurf prüfen
            </h2>
            <p className="mt-1 text-sm text-slate-500">
              {application.job_detail.title}
            </p>
          </div>
          <button
            type="button"
            className="rounded-lg p-2 text-slate-500 hover:bg-slate-100"
            onClick={onClose}
          >
            <X size={20} />
          </button>
        </div>
        {document ? (
          <DocumentEditor
            key={document.id}
            document={document}
            onSave={onSaveDocument}
            onApprove={onApproveDocument}
          />
        ) : (
          <EmptyState text="Für diese Bewerbung wurde noch kein Follow-up-Entwurf erstellt." />
        )}
      </div>
    </div>
  );
}

function KpiCard({ kpi, loading }: { kpi: Kpi; loading: boolean }) {
  const Icon = kpi.icon;
  return (
    <article className="card flex h-[112px] items-center gap-5 p-5">
      <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-full border border-blue-100 bg-blue-50 text-blue-600">
        <Icon size={27} strokeWidth={2.2} />
      </div>
      <div>
        <div className="text-sm font-medium text-slate-700">{kpi.label}</div>
        <div className="mt-1 text-[30px] font-bold leading-none tracking-[-0.04em]">
          {loading ? <LoadingText width="w-10" /> : kpi.value}
        </div>
        <div className="mt-2 text-xs font-medium text-slate-500">
          {kpi.subtitle}
        </div>
      </div>
    </article>
  );
}

function JobRankingPanel({
  jobs,
  selectedJobId,
  loading,
  onSelectJob,
}: {
  jobs: Job[];
  selectedJobId: number | null;
  loading: boolean;
  onSelectJob: (id: number) => void;
}) {
  return (
    <Panel className="p-0">
      <PanelHeader
        title="Job-Ranking"
        action={
          <button className="flex items-center gap-1 text-xs font-semibold text-slate-800">
            Nach Match-Score
            <ChevronDown size={14} />
          </button>
        }
      />
      <div className="space-y-3 px-3 pb-4">
        {loading ? (
          <SkeletonRows count={3} />
        ) : jobs.length ? (
          jobs.map((job) => (
            <JobCard
              key={job.apiId}
              job={job}
              selected={job.apiId === selectedJobId}
              onClick={() => job.apiId && onSelectJob(job.apiId)}
            />
          ))
        ) : (
          <EmptyState text="Noch keine Jobs gefunden. Starte eine Suchkampagne." />
        )}
      </div>
      <div className="border-t border-slate-100 px-5 py-4">
        <button className="inline-flex items-center gap-2 text-sm font-semibold text-blue-700">
          Alle gefundenen Jobs anzeigen
          <ArrowRight size={16} />
        </button>
      </div>
    </Panel>
  );
}

function JobCard({
  job,
  selected,
  onClick,
}: {
  job: Job;
  selected: boolean;
  onClick: () => void;
}) {
  return (
    <button
      className={cn(
        "w-full rounded-xl border bg-white p-3 text-left transition",
        selected
          ? "border-blue-500 shadow-[0_0_0_1px_rgba(37,99,235,0.18),0_14px_30px_rgba(15,23,42,0.07)]"
          : "border-slate-200 hover:border-blue-200 hover:shadow-sm",
      )}
      onClick={onClick}
    >
      <div className="grid grid-cols-[62px_1fr_74px_128px] items-center gap-3">
        <LogoMark label={job.logo} />
        <div className="min-w-0">
          <div className="truncate text-sm font-bold">{job.company}</div>
          <div className="truncate text-xs font-medium text-slate-700">
            {job.title}
          </div>
          <div className="mt-2 flex items-center gap-2">
            <span className="text-xs text-slate-500">
              {job.location} · {job.mode}
            </span>
            <div className="flex flex-wrap gap-1.5">
              {job.tags.slice(0, 4).map((tag) => (
                <span
                  key={tag}
                  className="rounded-md border border-slate-200 bg-slate-50 px-2 py-0.5 text-[11px] font-medium text-slate-700"
                >
                  {tag}
                </span>
              ))}
            </div>
          </div>
        </div>
        <ScoreBadge score={job.score} compact />
        <div className="flex items-center justify-between gap-2">
          <div>
            <StatusBadge label={job.status} tone={job.statusTone} />
            <div className="mt-1 text-[11px] text-slate-500">Nächste Aktion</div>
            <div className="text-xs font-medium text-slate-800">
              {job.nextAction}
            </div>
          </div>
          <ChevronRight size={16} className="text-slate-400" />
        </div>
      </div>
    </button>
  );
}

function JobDetailPanel({
  job,
  loading,
  actionState,
  onCreateApplication,
  onCreateGmailDraft,
}: {
  job: Job | null;
  loading: boolean;
  actionState: ActionState;
  onCreateApplication: (job: Job) => void;
  onCreateGmailDraft: (job: Job) => void;
}) {
  if (loading) {
    return (
      <Panel className="p-5">
        <LoadingText width="w-32" />
        <div className="mt-5">
          <SkeletonRows count={4} />
        </div>
      </Panel>
    );
  }

  if (!job) {
    return (
      <Panel className="p-5">
        <EmptyState text="Wähle einen Job aus, um die Detailprüfung zu sehen." />
      </Panel>
    );
  }

  const creatingApplication = actionState === "creating-application";
  const creatingDraft = actionState === "creating-draft";

  return (
    <Panel className="p-0">
      <PanelHeader
        title="Detailprüfung"
        action={
          <div className="flex items-center gap-3 text-slate-600">
            <Bookmark size={18} />
            <MoreVertical size={18} />
          </div>
        }
      />
      <div className="px-5 pb-5">
        <div className="grid grid-cols-[76px_1fr_86px] gap-4">
          <LogoMark label={job.logo} large />
          <div className="pt-1">
            <h2 className="text-lg font-bold tracking-[-0.02em]">{job.company}</h2>
            <p className="mt-1 text-sm font-medium text-slate-700">{job.title}</p>
            <p className="mt-2 text-xs text-slate-500">
              {job.location} · {job.mode}
              {job.published ? ` · Veröffentlicht: ${job.published}` : ""}
            </p>
          </div>
          <ScoreBadge score={job.score} />
        </div>
        <div className="mt-5 grid grid-cols-2 border-y border-slate-200">
          <DetailList title="Stärken" items={job.strengths} icon={Check} tone="green" />
          <DetailList
            title="Risiken"
            items={job.risks}
            icon={TriangleAlert}
            tone="orange"
            className="border-l border-slate-200 pl-5"
          />
        </div>
        <div className="mt-4 rounded-lg border border-blue-200 bg-blue-50/80 p-4">
          <div className="flex gap-3">
            <div className="mt-1 text-blue-700">
              <Sparkles size={22} />
            </div>
            <div>
              <div className="text-sm font-bold">Bewerbungswinkel</div>
              <p className="mt-1 text-sm leading-5 text-slate-700">"{job.angle}"</p>
            </div>
          </div>
        </div>
        <div className="mt-4 grid grid-cols-3 gap-3">
          <button
            className="inline-flex h-10 items-center justify-center gap-2 rounded-lg bg-blue-600 px-3 text-sm font-semibold text-white shadow-sm shadow-blue-200 hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-70"
            disabled={creatingApplication || creatingDraft}
            onClick={() => onCreateApplication(job)}
          >
            {creatingApplication ? <Loader2 size={16} className="animate-spin" /> : <PenLine size={16} />}
            Bewerbung erstellen
          </button>
          <button
            className="inline-flex h-10 items-center justify-center gap-2 rounded-lg border border-slate-200 bg-white px-3 text-sm font-semibold text-slate-800 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-70"
            disabled={creatingApplication || creatingDraft}
            onClick={() => onCreateGmailDraft(job)}
          >
            {creatingDraft ? <Loader2 size={16} className="animate-spin" /> : <MailIcon size={16} />}
            Gmail-Entwurf erstellen
          </button>
          <a
            className="inline-flex h-10 items-center justify-center gap-2 rounded-lg border border-slate-200 bg-white px-3 text-sm font-semibold text-slate-800 hover:bg-slate-50"
            href={job.sourceUrl || "#"}
            target="_blank"
            rel="noreferrer"
          >
            Stelle öffnen
            <ExternalLink size={15} />
          </a>
        </div>
      </div>
    </Panel>
  );
}

function DetailList({
  title,
  items,
  icon: Icon,
  tone,
  className,
}: {
  title: string;
  items: string[];
  icon: LucideIcon;
  tone: "green" | "orange";
  className?: string;
}) {
  return (
    <div className={cn("py-4", className)}>
      <h3 className="mb-3 text-sm font-bold">{title}</h3>
      <ul className="space-y-2.5">
        {items.map((item) => (
          <li key={item} className="flex gap-2 text-xs leading-5 text-slate-700">
            <Icon
              size={15}
              className={
                tone === "green"
                  ? "mt-0.5 shrink-0 text-emerald-600"
                  : "mt-0.5 shrink-0 text-orange-500"
              }
            />
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function CampaignsPanel({
  campaigns,
  loading,
}: {
  campaigns: DisplayCampaign[];
  loading: boolean;
}) {
  return (
    <Panel className="p-0">
      <PanelHeader title="Suchkampagnen" compact action={<PanelLink label="Alle anzeigen" />} />
      <div className="divide-y divide-slate-100">
        {loading ? (
          <SkeletonRows count={2} />
        ) : campaigns.length ? (
          campaigns.map((campaign) => (
            <div key={campaign.id} className="flex items-center gap-3 px-4 py-3">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-blue-100 bg-blue-50 text-blue-700">
                <Search size={18} />
              </div>
              <div className="min-w-0 flex-1">
                <div className="truncate text-sm font-bold">{campaign.title}</div>
                <div className="mt-0.5 text-xs text-slate-500">{campaign.meta}</div>
              </div>
              <div className="flex gap-2">
                {campaign.sources.slice(0, 2).map((source) => (
                  <span
                    key={source}
                    className="rounded-md border border-slate-200 bg-slate-50 px-2.5 py-1 text-[11px] font-semibold text-slate-700"
                  >
                    {source}
                  </span>
                ))}
              </div>
              <span className="rounded-md border border-blue-100 bg-blue-50 px-2.5 py-1 text-[11px] font-bold text-blue-700">
                {campaign.count}
              </span>
              <MoreVertical size={17} className="text-slate-400" />
            </div>
          ))
        ) : (
          <EmptyState text="Noch keine Suchkampagnen vorhanden." />
        )}
      </div>
    </Panel>
  );
}

function MailCenterPanel({
  mails,
  loading,
  syncing,
  onSync,
}: {
  mails: DisplayMail[];
  loading: boolean;
  syncing: boolean;
  onSync: () => void;
}) {
  return (
    <Panel className="p-0">
      <PanelHeader
        title="Mail- & Antwortzentrale"
        compact
        action={
          <button
            className="inline-flex items-center gap-1 text-xs font-semibold text-blue-700 disabled:opacity-60"
            disabled={syncing}
            onClick={onSync}
          >
            <RefreshCw size={14} className={syncing ? "animate-spin" : ""} />
            Synchronisieren
          </button>
        }
      />
      <div className="divide-y divide-slate-100">
        {loading ? (
          <SkeletonRows count={3} />
        ) : mails.length ? (
          mails.map((mail) => (
            <NavLink
              key={mail.id}
              className="grid grid-cols-[38px_1fr_auto_12px] items-center gap-3 px-4 py-3"
              to="/mail"
            >
              <div
                className={cn(
                  "flex h-9 w-9 items-center justify-center rounded-full text-sm font-bold",
                  mail.tone === "green" && "bg-blue-50 text-blue-700",
                  mail.tone === "orange" && "bg-violet-50 text-violet-700",
                  mail.tone === "red" && "bg-rose-50 text-rose-700",
                  mail.tone === "gray" && "bg-slate-50 text-slate-600",
                )}
              >
                {mail.initials}
              </div>
              <div className="min-w-0">
                <div className="truncate text-sm font-bold">{mail.sender}</div>
                <div className="truncate text-xs text-slate-500">{mail.subject}</div>
              </div>
              <StatusBadge label={mail.badge} tone={mail.tone} />
              <span className="h-1.5 w-1.5 rounded-full bg-blue-600" />
            </NavLink>
          ))
        ) : (
          <EmptyState text="Noch keine E-Mails synchronisiert." />
        )}
      </div>
    </Panel>
  );
}

function PipelineBoard({
  columns,
  loading,
}: {
  columns: PipelineColumn[];
  loading: boolean;
}) {
  return (
    <Panel className="p-0">
      <PanelHeader title="Bewerbungs-Pipeline" compact />
      <div className="grid grid-cols-4 gap-4 px-4 pb-4">
        {loading
          ? Array.from({ length: 4 }).map((_, index) => (
              <div key={index} className="h-32 rounded-lg bg-slate-100/80" />
            ))
          : columns.map((column) => (
              <div key={column.title} className="overflow-hidden rounded-lg border border-slate-200 bg-white">
                <div
                  className={cn(
                    "flex items-center justify-between px-3 py-2 text-sm font-bold",
                    column.tone === "blue" && "bg-blue-50 text-slate-900",
                    column.tone === "orange" && "bg-amber-50 text-slate-900",
                    column.tone === "green" && "bg-emerald-50 text-emerald-900",
                    column.tone === "purple" && "bg-violet-50 text-slate-900",
                  )}
                >
                  <span>{column.title}</span>
                  <span className="rounded-full bg-white/80 px-2 text-xs text-blue-700">
                    {column.count}
                  </span>
                </div>
                <div className="divide-y divide-slate-100">
                  {column.cards.length ? (
                    column.cards.map((card) => (
                      <NavLink
                        key={card.id}
                        className="grid grid-cols-[1fr_auto] gap-2 px-3 py-3 transition hover:bg-blue-50"
                        to={`/bewerbungen/${card.id}`}
                      >
                        <div className="min-w-0">
                          <div className="truncate text-xs font-bold">{card.title}</div>
                          <div className="mt-1 truncate text-[11px] text-slate-500">
                            {card.subtitle}
                          </div>
                        </div>
                        <div className="pt-4 text-[11px] text-slate-500">{card.date}</div>
                      </NavLink>
                    ))
                  ) : (
                    <div className="px-3 py-5 text-xs text-slate-500">Keine Karten</div>
                  )}
                </div>
              </div>
            ))}
      </div>
    </Panel>
  );
}

function TodayImportantPanel({
  items,
  loading,
}: {
  items: TodayItem[];
  loading: boolean;
}) {
  return (
    <Panel className="p-0">
      <PanelHeader title="Heute wichtig" compact />
      <div className="space-y-3 px-4 pb-4">
        {loading ? (
          <SkeletonRows count={3} />
        ) : (
          items.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.title}
                to={item.path ?? "/"}
                className="grid w-full grid-cols-[44px_1fr_34px_18px] items-center gap-3 rounded-lg border border-slate-100 bg-white px-3 py-3 text-left transition hover:border-blue-200 hover:shadow-sm"
              >
                <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-blue-100 bg-blue-50 text-blue-700">
                  <Icon size={18} />
                </div>
                <div className="min-w-0">
                  <div className="truncate text-sm font-bold">{item.title}</div>
                  <div className="mt-1 truncate text-xs text-slate-500">
                    {item.subtitle}
                  </div>
                </div>
                <span className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-100 text-sm font-bold text-slate-700">
                  {item.count}
                </span>
                <ChevronRight size={17} className="text-slate-500" />
              </NavLink>
            );
          })
        )}
      </div>
      <div className="border-t border-slate-100 px-5 py-4">
        <button className="inline-flex items-center gap-2 text-sm font-semibold text-blue-700">
          Alle Aufgaben anzeigen
          <ArrowRight size={16} />
        </button>
      </div>
    </Panel>
  );
}

function CampaignModal({
  submitting,
  onClose,
  onSubmit,
}: {
  submitting: boolean;
  onClose: () => void;
  onSubmit: (form: CampaignFormState) => void;
}) {
  const [form, setForm] = useState(defaultCampaignForm);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onSubmit(form);
  }

  return (
    <div className="fixed inset-0 z-20 flex items-center justify-center bg-slate-950/35 px-4">
      <form
        className="w-full max-w-2xl rounded-2xl border border-slate-200 bg-white p-6 shadow-2xl"
        onSubmit={handleSubmit}
      >
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-xl font-bold tracking-[-0.02em]">Neue Suchkampagne</h2>
            <p className="mt-1 text-sm text-slate-500">
              Erstellt eine Kampagne und startet direkt die mock-basierte Jobsuche.
            </p>
          </div>
          <button
            type="button"
            className="rounded-lg p-2 text-slate-500 hover:bg-slate-100"
            onClick={onClose}
          >
            <X size={20} />
          </button>
        </div>
        <div className="mt-6 grid grid-cols-2 gap-4">
          <TextField
            label="Name"
            value={form.name}
            onChange={(value) => setForm({ ...form, name: value })}
          />
          <TextField
            label="Standort"
            value={form.location}
            onChange={(value) => setForm({ ...form, location: value })}
          />
          <TextField
            label="Keywords"
            value={form.keywords}
            onChange={(value) => setForm({ ...form, keywords: value })}
          />
          <TextField
            label="Branchen"
            value={form.industries}
            onChange={(value) => setForm({ ...form, industries: value })}
          />
          <TextField
            label="Ausschlüsse"
            value={form.exclude_keywords}
            onChange={(value) => setForm({ ...form, exclude_keywords: value })}
          />
          <fieldset className="col-span-2 rounded-xl border border-slate-200 p-4">
            <legend className="px-1 text-xs font-bold text-slate-600">Quellen</legend>
            <div className="grid grid-cols-3 gap-3">
              {campaignSources.map((source) => {
                const checked = form.sources.includes(source);
                return (
                  <label
                    key={source}
                    className={cn(
                      "flex items-center gap-2 rounded-lg border px-3 py-2 text-sm font-semibold",
                      checked
                        ? "border-blue-200 bg-blue-50 text-blue-800"
                        : "border-slate-200 bg-white text-slate-700",
                    )}
                  >
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={(event) =>
                        setForm({
                          ...form,
                          sources: event.target.checked
                            ? [...form.sources, source]
                            : form.sources.filter((item) => item !== source),
                        })
                      }
                    />
                    {source}
                  </label>
                );
              })}
            </div>
          </fieldset>
          <label className="block">
            <span className="text-xs font-bold text-slate-600">Radius km</span>
            <input
              className="mt-1 h-10 w-full rounded-lg border border-slate-200 px-3 text-sm outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
              min={0}
              type="number"
              value={form.radius_km}
              onChange={(event) =>
                setForm({ ...form, radius_km: Number(event.target.value) })
              }
            />
          </label>
          <div className="flex items-end gap-4">
            <label className="flex items-center gap-2 text-sm font-semibold text-slate-700">
              <input
                type="checkbox"
                checked={form.remote_allowed}
                onChange={(event) =>
                  setForm({ ...form, remote_allowed: event.target.checked })
                }
              />
              Remote erlaubt
            </label>
            <label className="flex items-center gap-2 text-sm font-semibold text-slate-700">
              <input
                type="checkbox"
                checked={form.hybrid_allowed}
                onChange={(event) =>
                  setForm({ ...form, hybrid_allowed: event.target.checked })
                }
              />
              Hybrid erlaubt
            </label>
          </div>
        </div>
        <div className="mt-6 flex justify-end gap-3">
          <button
            type="button"
            className="h-10 rounded-lg border border-slate-200 bg-white px-4 text-sm font-semibold text-slate-800 hover:bg-slate-50"
            onClick={onClose}
          >
            Abbrechen
          </button>
          <button
            className="inline-flex h-10 items-center gap-2 rounded-lg bg-blue-600 px-4 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-70"
            disabled={submitting}
          >
            {submitting ? <Loader2 size={16} className="animate-spin" /> : <Plus size={16} />}
            Erstellen & starten
          </button>
        </div>
      </form>
    </div>
  );
}

function ManualJobModal({
  submitting,
  onClose,
  onSubmit,
}: {
  submitting: boolean;
  onClose: () => void;
  onSubmit: (form: ManualJobFormState) => void;
}) {
  const [form, setForm] = useState(defaultManualJobForm);
  const [error, setError] = useState<string | null>(null);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!form.company.trim() || !form.title.trim() || !form.description.trim()) {
      setError("Firma, Jobtitel und Stellenbeschreibung sind Pflichtfelder.");
      return;
    }
    setError(null);
    onSubmit(form);
  }

  return (
    <div className="fixed inset-0 z-20 flex items-center justify-center bg-slate-950/35 px-4 py-8">
      <form
        className="max-h-[92vh] w-full max-w-4xl overflow-auto rounded-2xl border border-slate-200 bg-white p-6 shadow-2xl"
        onSubmit={handleSubmit}
      >
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-xl font-bold tracking-[-0.02em]">
              Stelle manuell hinzufügen
            </h2>
            <p className="mt-1 text-sm text-slate-500">
              Füge eine reale Stellenanzeige ein. Die Bewertung bleibt mock-basiert.
            </p>
          </div>
          <button
            type="button"
            className="rounded-lg p-2 text-slate-500 hover:bg-slate-100"
            onClick={onClose}
          >
            <X size={20} />
          </button>
        </div>

        {error ? (
          <div className="mt-4 rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm font-semibold text-rose-800">
            {error}
          </div>
        ) : null}

        <div className="mt-6 grid grid-cols-2 gap-4">
          <TextField
            label="Firma *"
            value={form.company}
            onChange={(value) => setForm({ ...form, company: value })}
          />
          <TextField
            label="Jobtitel *"
            value={form.title}
            onChange={(value) => setForm({ ...form, title: value })}
          />
          <TextField
            label="Standort"
            value={form.location}
            onChange={(value) => setForm({ ...form, location: value })}
          />
          <TextField
            label="Quelle"
            value={form.source}
            onChange={(value) => setForm({ ...form, source: value })}
          />
          <TextField
            label="Stellenanzeige-URL"
            value={form.source_url}
            onChange={(value) => setForm({ ...form, source_url: value })}
          />
          <TextField
            label="Beschäftigungsart"
            value={form.employment_type}
            onChange={(value) => setForm({ ...form, employment_type: value })}
          />
          <TextField
            label="Remote-Modell"
            value={form.remote_type}
            onChange={(value) => setForm({ ...form, remote_type: value })}
          />
          <TextField
            label="Tags"
            value={form.tags}
            onChange={(value) => setForm({ ...form, tags: value })}
          />
          <TextField
            label="Anforderungen"
            value={form.requirements}
            onChange={(value) => setForm({ ...form, requirements: value })}
          />
          <TextField
            label="Nice-to-have"
            value={form.nice_to_have}
            onChange={(value) => setForm({ ...form, nice_to_have: value })}
          />
          <label className="col-span-2 block">
            <span className="text-xs font-bold text-slate-600">
              Vollständige Stellenbeschreibung *
            </span>
            <textarea
              className="mt-1 min-h-[220px] w-full rounded-lg border border-slate-200 p-4 text-sm leading-6 outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
              value={form.description}
              onChange={(event) =>
                setForm({ ...form, description: event.target.value })
              }
            />
          </label>
        </div>
        <p className="mt-3 text-xs font-medium text-slate-500">
          Anforderungen, Nice-to-have und Tags werden kommagetrennt eingegeben.
        </p>
        <div className="mt-6 flex justify-end gap-3">
          <button
            type="button"
            className="h-10 rounded-lg border border-slate-200 bg-white px-4 text-sm font-semibold text-slate-800 hover:bg-slate-50"
            onClick={onClose}
          >
            Abbrechen
          </button>
          <button
            className="inline-flex h-10 items-center gap-2 rounded-lg bg-blue-600 px-4 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-70"
            disabled={submitting}
          >
            {submitting ? <Loader2 size={16} className="animate-spin" /> : <Plus size={16} />}
            Speichern & bewerten
          </button>
        </div>
      </form>
    </div>
  );
}

function ApplicationReviewPage() {
  const params = useParams();
  const applicationId = Number(params.id);
  const [application, setApplication] = useState<ApplicationDto | null>(null);
  const [loading, setLoading] = useState(true);
  const [notice, setNotice] = useState<Notice | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const loadApplication = useCallback(async () => {
    if (!Number.isFinite(applicationId)) return;
    setLoading(true);
    try {
      setApplication(await getApplication(applicationId));
    } catch (error) {
      setNotice({ type: "error", text: readableError(error) });
    } finally {
      setLoading(false);
    }
  }, [applicationId]);

  useEffect(() => {
    void loadApplication();
  }, [loadApplication]);

  async function handleSaveDocument(
    document: ApplicationDocumentDto,
    payload: Pick<ApplicationDocumentDto, "title" | "content">,
  ) {
    if (!application) return;
    try {
      await updateApplicationDocument(application.id, document.id, payload);
      await loadApplication();
      setNotice({ type: "success", text: "Dokument wurde gespeichert." });
    } catch (error) {
      setNotice({ type: "error", text: readableError(error) });
    }
  }

  async function handleApproveDocument(document: ApplicationDocumentDto) {
    if (!application) return;
    try {
      await approveApplicationDocument(application.id, document.id);
      await loadApplication();
      setNotice({ type: "success", text: "Entwurf wurde freigegeben." });
    } catch (error) {
      setNotice({ type: "error", text: readableError(error) });
    }
  }

  async function handleCreateDraft() {
    if (!application) return;
    setSubmitting(true);
    try {
      await createGmailDraft(application.id);
      await loadApplication();
      setNotice({ type: "success", text: "Gmail-Entwurf wurde simuliert erstellt." });
    } catch (error) {
      setNotice({ type: "error", text: readableError(error) });
    } finally {
      setSubmitting(false);
    }
  }

  async function handleUpdateApplication(payload: UpdateApplicationPayload) {
    if (!application) return;
    setSubmitting(true);
    try {
      await updateApplication(application.id, payload);
      await loadApplication();
      setNotice({ type: "success", text: "Bewerbung wurde aktualisiert." });
    } catch (error) {
      setNotice({ type: "error", text: readableError(error) });
    } finally {
      setSubmitting(false);
    }
  }

  async function handleMarkApplied() {
    if (!application) return;
    setSubmitting(true);
    try {
      await markApplicationApplied(application.id);
      await loadApplication();
      setNotice({ type: "success", text: "Bewerbung wurde als beworben markiert." });
    } catch (error) {
      setNotice({ type: "error", text: readableError(error) });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-[1504px] px-8 py-7">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-[28px] font-bold tracking-[-0.03em]">
            Bewerbungsdetail
          </h1>
          <p className="mt-1 text-sm font-medium text-slate-500">
            Dokumente, Status, Notizen und Follow-up verwalten.
          </p>
        </div>
        <NavLink
          className="inline-flex h-11 items-center gap-2 rounded-lg border border-slate-200 bg-white px-5 text-sm font-semibold text-slate-800 shadow-sm transition hover:bg-slate-50"
          to="/bewerbungen"
        >
          Zur Bewerbungsliste
        </NavLink>
      </header>
      {notice ? <NoticeBanner notice={notice} onDismiss={() => setNotice(null)} /> : null}
      {loading ? (
        <section className="card mt-6 p-8">
          <LoadingText width="w-40" />
          <div className="mt-5">
            <SkeletonRows count={4} />
          </div>
        </section>
      ) : application ? (
        <ApplicationReviewCard
          application={application}
          submitting={submitting}
          onSaveDocument={handleSaveDocument}
          onApproveDocument={handleApproveDocument}
          onCreateGmailDraft={handleCreateDraft}
          onUpdateApplication={handleUpdateApplication}
          onMarkApplied={handleMarkApplied}
        />
      ) : (
        <ErrorState message="Bewerbung wurde nicht gefunden." onRetry={loadApplication} />
      )}
    </div>
  );
}

function ApplicationReviewModal({
  application,
  submitting,
  onClose,
  onSaveDocument,
  onApproveDocument,
  onCreateGmailDraft,
}: {
  application: ApplicationDto;
  submitting: boolean;
  onClose: () => void;
  onSaveDocument: (
    document: ApplicationDocumentDto,
    payload: Pick<ApplicationDocumentDto, "title" | "content">,
  ) => void;
  onApproveDocument: (document: ApplicationDocumentDto) => void;
  onCreateGmailDraft: () => void;
}) {
  return (
    <div className="fixed inset-0 z-20 flex items-center justify-center bg-slate-950/35 px-4 py-8">
      <div className="max-h-[92vh] w-full max-w-5xl overflow-auto rounded-2xl border border-slate-200 bg-white p-6 shadow-2xl">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-xl font-bold tracking-[-0.02em]">
              Bewerbungsunterlagen prüfen
            </h2>
            <p className="mt-1 text-sm text-slate-500">
              Prüfe und bearbeite die generierten Dokumente, bevor ein Gmail-Entwurf
              simuliert wird.
            </p>
          </div>
          <button
            type="button"
            className="rounded-lg p-2 text-slate-500 hover:bg-slate-100"
            onClick={onClose}
          >
            <X size={20} />
          </button>
        </div>
        <ApplicationReviewCard
          application={application}
          submitting={submitting}
          onSaveDocument={onSaveDocument}
          onApproveDocument={onApproveDocument}
          onCreateGmailDraft={onCreateGmailDraft}
        />
      </div>
    </div>
  );
}

function ApplicationReviewCard({
  application,
  submitting,
  onSaveDocument,
  onApproveDocument,
  onCreateGmailDraft,
  onUpdateApplication,
  onMarkApplied,
}: {
  application: ApplicationDto;
  submitting: boolean;
  onSaveDocument: (
    document: ApplicationDocumentDto,
    payload: Pick<ApplicationDocumentDto, "title" | "content">,
  ) => void;
  onApproveDocument: (document: ApplicationDocumentDto) => void;
  onCreateGmailDraft: () => void;
  onUpdateApplication?: (payload: UpdateApplicationPayload) => void;
  onMarkApplied?: () => void;
}) {
  const [activeType, setActiveType] = useState<ReviewDocumentType>("cover_letter");
  const documents = getLatestReviewDocuments(application);
  const activeDocument = documents[activeType];
  const approvedEmail = documents.email?.is_approved ?? false;

  return (
    <section className="card mt-5 p-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="text-sm font-semibold text-slate-500">
            {application.job_detail.company}
          </div>
          <h1 className="mt-1 text-xl font-bold tracking-[-0.02em]">
            {application.job_detail.title}
          </h1>
          <div className="mt-2 flex items-center gap-2">
            <StatusBadge
              label={applicationStatusLabel(application.status)}
              tone={applicationStatusTone(application.status)}
            />
          </div>
        </div>
        <button
          className="inline-flex h-10 items-center gap-2 rounded-lg bg-blue-600 px-4 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-70"
          disabled={submitting || !approvedEmail}
          onClick={onCreateGmailDraft}
        >
          {submitting ? <Loader2 size={16} className="animate-spin" /> : <MailIcon size={16} />}
          Gmail-Entwurf erstellen
        </button>
      </div>
      {!approvedEmail ? (
        <div className="mt-4 rounded-lg border border-orange-200 bg-orange-50 px-4 py-3 text-sm font-semibold text-orange-800">
          Bitte prüfe und bestätige zuerst den E-Mail-Entwurf.
        </div>
      ) : null}
      {onUpdateApplication && onMarkApplied ? (
        <ApplicationManagementControls
          application={application}
          submitting={submitting}
          onUpdateApplication={onUpdateApplication}
          onMarkApplied={onMarkApplied}
        />
      ) : null}
      <div className="mt-5 flex gap-2 border-b border-slate-200">
        {[
          ["cover_letter", "Anschreiben"],
          ["email", "E-Mail"],
        ].map(([type, label]) => (
          <button
            key={type}
            className={cn(
              "border-b-2 px-4 py-2 text-sm font-bold",
              activeType === type
                ? "border-blue-600 text-blue-700"
                : "border-transparent text-slate-500 hover:text-slate-800",
            )}
            onClick={() => setActiveType(type as ReviewDocumentType)}
          >
            {label}
          </button>
        ))}
      </div>
      {activeDocument ? (
        <DocumentEditor
          key={activeDocument.id}
          document={activeDocument}
          onSave={onSaveDocument}
          onApprove={onApproveDocument}
        />
      ) : (
        <EmptyState text="Für diesen Dokumenttyp wurde noch kein Entwurf erzeugt." />
      )}
    </section>
  );
}

function ApplicationManagementControls({
  application,
  submitting,
  onUpdateApplication,
  onMarkApplied,
}: {
  application: ApplicationDto;
  submitting: boolean;
  onUpdateApplication: (payload: UpdateApplicationPayload) => void;
  onMarkApplied: () => void;
}) {
  const [notes, setNotes] = useState(application.notes ?? "");
  const [followUpDate, setFollowUpDate] = useState(dateInputValue(application.follow_up_at));
  const notesDirty = notes !== (application.notes ?? "");
  const followUpDirty = followUpDate !== dateInputValue(application.follow_up_at);
  const due = isFollowUpDue(application.follow_up_at);

  useEffect(() => {
    setNotes(application.notes ?? "");
    setFollowUpDate(dateInputValue(application.follow_up_at));
  }, [application.follow_up_at, application.notes]);

  return (
    <div className="mt-5 grid grid-cols-[1fr_360px] gap-4">
      <div className="rounded-xl border border-slate-100 bg-slate-50 p-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold">Notizen</h2>
          <button
            className="h-9 rounded-lg bg-blue-600 px-3 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-60"
            disabled={submitting || !notesDirty}
            onClick={() => onUpdateApplication({ notes })}
          >
            Notizen speichern
          </button>
        </div>
        <textarea
          className="mt-3 min-h-[130px] w-full rounded-lg border border-slate-200 bg-white p-3 text-sm leading-6 outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
          value={notes}
          onChange={(event) => setNotes(event.target.value)}
        />
      </div>
      <div className="rounded-xl border border-slate-100 bg-white p-4">
        <h2 className="text-sm font-bold">Aktionen</h2>
        <div className="mt-3 space-y-3">
          <label
            className={cn(
              "block rounded-lg border p-3",
              due ? "border-orange-200 bg-orange-50" : "border-slate-200 bg-slate-50",
            )}
          >
            <span className="text-xs font-bold text-slate-600">
              Follow-up-Datum setzen
            </span>
            <input
              className="mt-2 h-10 w-full rounded-lg border border-slate-200 bg-white px-3 text-sm outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
              type="date"
              value={followUpDate}
              onChange={(event) => setFollowUpDate(event.target.value)}
            />
            {due ? (
              <span className="mt-2 block text-xs font-bold text-orange-800">
                Follow-up ist fällig.
              </span>
            ) : null}
          </label>
          <button
            className="h-10 w-full rounded-lg border border-slate-200 bg-white px-3 text-sm font-semibold text-slate-800 hover:bg-slate-50 disabled:opacity-60"
            disabled={submitting || !followUpDirty}
            onClick={() =>
              onUpdateApplication({ follow_up_at: dateInputToDateTime(followUpDate) })
            }
          >
            Follow-up speichern
          </button>
          <button
            className="inline-flex h-10 w-full items-center justify-center gap-2 rounded-lg border border-slate-200 bg-white px-3 text-sm font-semibold text-slate-800 hover:bg-slate-50 disabled:opacity-60"
            disabled={submitting || application.status === "applied"}
            onClick={onMarkApplied}
          >
            <Send size={15} />
            Als beworben markieren
          </button>
          <button
            className="h-10 w-full rounded-lg border border-slate-200 bg-white px-3 text-sm font-semibold text-slate-800 hover:bg-slate-50 disabled:opacity-60"
            disabled={submitting || application.status === "follow_up_due"}
            onClick={() => onUpdateApplication({ status: "follow_up_due" })}
          >
            Follow-up setzen
          </button>
          <button
            className="h-10 w-full rounded-lg border border-slate-200 bg-white px-3 text-sm font-semibold text-slate-800 hover:bg-slate-50 disabled:opacity-60"
            disabled={submitting || application.status === "closed"}
            onClick={() => onUpdateApplication({ status: "closed" })}
          >
            Als abgeschlossen markieren
          </button>
        </div>
      </div>
      <div className="col-span-2 rounded-xl border border-slate-100 bg-white p-4">
        <h2 className="text-sm font-bold">Statusverlauf</h2>
        <div className="mt-3 divide-y divide-slate-100">
          {application.status_events.length ? (
            application.status_events.map((event) => (
              <div key={event.id} className="grid grid-cols-[170px_1fr] gap-4 py-3 text-sm">
                <div className="font-semibold text-slate-500">
                  {formatNullableDate(event.created_at)}
                </div>
                <div>
                  <div className="font-bold text-slate-800">
                    {event.old_status ? applicationStatusText(event.old_status) : "Start"} →{" "}
                    {applicationStatusText(event.new_status)}
                  </div>
                  <div className="mt-1 text-slate-500">{event.note}</div>
                </div>
              </div>
            ))
          ) : (
            <div className="py-4 text-sm font-medium text-slate-500">
              Noch keine Statusereignisse vorhanden.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function DocumentEditor({
  document,
  onSave,
  onApprove,
}: {
  document: ApplicationDocumentDto;
  onSave: (
    document: ApplicationDocumentDto,
    payload: Pick<ApplicationDocumentDto, "title" | "content">,
  ) => void;
  onApprove: (document: ApplicationDocumentDto) => void;
}) {
  const [title, setTitle] = useState(document.title);
  const [content, setContent] = useState(document.content);
  const dirty = title !== document.title || content !== document.content;

  useEffect(() => {
    setTitle(document.title);
    setContent(document.content);
  }, [document]);

  return (
    <div className="mt-5">
      <div className="mb-3 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <StatusBadge
            label={document.is_approved ? "Freigegeben" : "Prüfung offen"}
            tone={document.is_approved ? "green" : "orange"}
          />
          <span className="text-xs font-semibold text-slate-500">
            Version {document.version}
          </span>
        </div>
        {dirty ? (
          <span className="text-xs font-semibold text-orange-700">
            Änderungen noch nicht gespeichert
          </span>
        ) : null}
      </div>
      <label className="block">
        <span className="text-xs font-bold text-slate-600">Dokumenttitel</span>
        <input
          className="mt-1 h-10 w-full rounded-lg border border-slate-200 px-3 text-sm font-semibold outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
          value={title}
          onChange={(event) => setTitle(event.target.value)}
        />
      </label>
      <label className="mt-4 block">
        <span className="text-xs font-bold text-slate-600">Inhalt</span>
        <textarea
          className="mt-1 min-h-[360px] w-full rounded-lg border border-slate-200 p-4 text-sm leading-6 outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
          value={content}
          onChange={(event) => setContent(event.target.value)}
        />
      </label>
      <div className="mt-4 flex justify-end gap-3">
        <button
          className="h-10 rounded-lg border border-slate-200 bg-white px-4 text-sm font-semibold text-slate-800 hover:bg-slate-50 disabled:opacity-60"
          disabled={!dirty}
          onClick={() => onSave(document, { title, content })}
        >
          Speichern
        </button>
        <button
          className="inline-flex h-10 items-center gap-2 rounded-lg bg-blue-600 px-4 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-60"
          disabled={dirty || document.is_approved}
          onClick={() => onApprove(document)}
        >
          <Check size={16} />
          Entwurf freigeben
        </button>
      </div>
    </div>
  );
}

function TextField({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <label className="block">
      <span className="text-xs font-bold text-slate-600">{label}</span>
      <input
        className="mt-1 h-10 w-full rounded-lg border border-slate-200 px-3 text-sm outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
        value={value}
        onChange={(event) => onChange(event.target.value)}
      />
    </label>
  );
}

function NoticeBanner({
  notice,
  onDismiss,
}: {
  notice: Notice;
  onDismiss: () => void;
}) {
  return (
    <div
      className={cn(
        "mt-5 flex items-center justify-between rounded-xl border px-4 py-3 text-sm font-semibold",
        notice.type === "success"
          ? "border-emerald-200 bg-emerald-50 text-emerald-800"
          : "border-rose-200 bg-rose-50 text-rose-800",
      )}
    >
      <span>{notice.text}</span>
      <button onClick={onDismiss}>
        <X size={18} />
      </button>
    </div>
  );
}

function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <section className="card mt-6 p-8">
      <div className="max-w-xl">
        <h2 className="text-xl font-bold">Backend nicht erreichbar</h2>
        <p className="mt-2 text-sm leading-6 text-slate-600">
          Die Oberfläche konnte keine Daten vom Django REST Backend laden. Prüfe, ob
          der Server unter `http://127.0.0.1:8000` läuft und CORS korrekt gesetzt ist.
        </p>
        <p className="mt-3 rounded-lg bg-rose-50 px-3 py-2 text-sm font-medium text-rose-700">
          {message}
        </p>
        <button
          className="mt-5 inline-flex h-10 items-center gap-2 rounded-lg bg-blue-600 px-4 text-sm font-semibold text-white hover:bg-blue-700"
          onClick={onRetry}
        >
          <RefreshCw size={16} />
          Erneut versuchen
        </button>
      </div>
    </section>
  );
}

function Panel({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return <section className={cn("card", className)}>{children}</section>;
}

function PanelHeader({
  title,
  action,
  compact = false,
}: {
  title: string;
  action?: ReactNode;
  compact?: boolean;
}) {
  return (
    <div className={cn("flex items-center justify-between", compact ? "px-4 py-3" : "px-5 py-4")}>
      <h2 className="text-base font-bold tracking-[-0.02em]">{title}</h2>
      {action}
    </div>
  );
}

function PanelLink({ label }: { label: string }) {
  return (
    <button className="inline-flex items-center gap-1 text-xs font-semibold text-blue-700">
      {label}
      <ArrowRight size={14} />
    </button>
  );
}

function EmptyState({ text }: { text: string }) {
  return <div className="px-4 py-8 text-sm font-medium text-slate-500">{text}</div>;
}

function SkeletonRows({ count }: { count: number }) {
  return (
    <>
      {Array.from({ length: count }).map((_, index) => (
        <div key={index} className="mx-3 my-3 h-16 animate-pulse rounded-xl bg-slate-100" />
      ))}
    </>
  );
}

function LoadingText({ width }: { width: string }) {
  return <span className={cn("inline-block h-7 animate-pulse rounded bg-slate-100", width)} />;
}

function LogoMark({ label, large = false }: { label: string; large?: boolean }) {
  return (
    <div
      className={cn(
        "flex shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-slate-950 via-blue-950 to-sky-700 font-bold text-white shadow-inner",
        large ? "h-[76px] w-[76px] text-[13px]" : "h-[56px] w-[56px] text-[11px]",
      )}
    >
      {label}
    </div>
  );
}

function ScoreBadge({ score, compact = false }: { score: number; compact?: boolean }) {
  return (
    <div className="flex flex-col items-center">
      <div
        className={cn(
          "flex items-center justify-center rounded-full border-2 border-emerald-500 bg-white font-bold text-emerald-800",
          compact ? "h-11 w-11 text-sm" : "h-16 w-16 text-xl",
        )}
      >
        {score}%
      </div>
      <div className={cn("mt-1 text-slate-500", compact ? "text-[10px]" : "text-xs")}>
        Match-Score
      </div>
    </div>
  );
}

function StatusBadge({ label, tone }: { label: string; tone: StatusTone }) {
  return (
    <span className="inline-flex items-center gap-1.5 text-xs font-bold text-slate-800">
      <span className={cn("h-1.5 w-1.5 rounded-full", dotStyles[tone])} />
      <span className={cn("rounded-md border px-2 py-0.5", toneStyles[tone])}>
        {label}
      </span>
    </span>
  );
}

function getLatestReviewDocuments(application: ApplicationDto) {
  return application.documents.reduce<
    Partial<Record<ReviewDocumentType, ApplicationDocumentDto>>
  >((documents, document) => {
    if (document.document_type !== "cover_letter" && document.document_type !== "email") {
      return documents;
    }
    const existing = documents[document.document_type];
    if (!existing || document.version > existing.version) {
      documents[document.document_type] = document;
    }
    return documents;
  }, {});
}

function buildKpis(
  summary: DashboardSummary | null,
  jobs: JobPostingDto[],
  applications: ApplicationDto[],
  mailMessages: EmailMessageDto[],
): Kpi[] {
  const kpis = summary?.kpis;
  const draftCount =
    kpis?.open_drafts ??
    countStatus(applications, ["draft_open", "draft_approved", "gmail_draft_created"]);
  const appliedCount =
    kpis?.applied_count ??
    countStatus(applications, [
      "applied",
      "response_received",
      "interview",
      "rejected",
      "follow_up_due",
      "closed",
    ]);
  const responseCount =
    kpis?.responses_count ??
    mailMessages.filter(
      (message) => message.application !== null && message.classification !== "unknown",
    ).length;
  const followUpCount =
    kpis?.followups_due ??
    applications.filter((application) =>
      isApplicationFollowUpDue(
        application,
        latestMailForApplication(application.id, mailMessages),
      ),
    ).length;
  const newMatchingJobs =
    kpis?.new_matching_jobs ??
    jobs.filter((job) => (job.match?.score ?? 0) >= 75).length;

  return [
    {
      label: "Neue passende Jobs",
      value: String(newMatchingJobs),
      subtitle: "Aus dem Backend",
      icon: BriefcaseBusiness,
    },
    {
      label: "Entwürfe offen",
      value: String(draftCount),
      subtitle: "Bewerbungen",
      icon: FileText,
    },
    {
      label: "Beworben",
      value: String(appliedCount),
      subtitle: "Gesamt",
      icon: Send,
    },
    {
      label: "Antworten",
      value: String(responseCount),
      subtitle: "Mail-Zentrale",
      icon: Mail,
    },
    {
      label: "Follow-ups fällig",
      value: String(followUpCount),
      subtitle: "Nächste 7 Tage",
      icon: Bell,
    },
  ];
}

function mapJob(job: JobPostingDto, applications: ApplicationDto[]): Job {
  const application = applications.find((item) => item.job === job.id);
  const status = application ? applicationStatusLabel(application.status) : "Neu gefunden";
  const statusTone = application ? applicationStatusTone(application.status) : "orange";
  const requirements = [...(job.requirements ?? []), ...(job.nice_to_have ?? [])];
  return {
    id: String(job.id),
    apiId: job.id,
    applicationId: application?.id,
    logo: logoForCompany(job.company),
    company: job.company,
    title: job.title,
    location: job.location || "Unbekannt",
    mode: remoteTypeLabel(job.remote_type),
    published: formatDate(job.published_at),
    tags: job.tags?.length ? job.tags : requirements.slice(0, 4),
    score: job.match?.score ?? 0,
    status,
    statusTone,
    nextAction: nextActionForStatus(application?.status),
    strengths: job.match?.strengths?.length
      ? job.match.strengths
      : [
          "Profil passt grundsätzlich zur Stellenbeschreibung",
          "Anforderungen lassen sich manuell prüfen",
        ],
    risks: job.match?.risks?.length
      ? job.match.risks
      : ["Match wurde noch nicht bewertet", "Bitte Anforderungen im Detail prüfen"],
    angle:
      job.match?.application_angle ||
      "Fokus auf praktische Webentwicklung, Automatisierung und schnelle Einarbeitung legen.",
    sourceUrl: job.source_url,
  };
}

function mapCampaign(campaign: SearchCampaignDto): DisplayCampaign {
  return {
    id: campaign.id,
    title: campaign.name,
    meta: `${campaign.location || "Deutschland"} · ${
      campaign.remote_allowed ? "Remote" : campaign.hybrid_allowed ? "Hybrid" : "Vor Ort"
    }`,
    sources: campaign.sources,
    count: campaign.status === "active" ? "aktiv" : statusLabel(campaign.status),
  };
}

function mapMail(message: EmailMessageDto): DisplayMail {
  const sender = message.sender.includes("@")
    ? message.sender.split("@")[0].replace(/[._-]/g, " ")
    : message.sender;
  return {
    id: message.id,
    sender: titleCase(sender),
    subject: message.subject,
    badge: classificationLabel(message.classification),
    tone: classificationTone(message.classification),
    initials: initialsFrom(sender),
  };
}

function buildPipeline(applications: ApplicationDto[]): PipelineColumn[] {
  const groups = [
    {
      title: "Neu",
      tone: "blue" as const,
      statuses: ["new", "interesting"] as ApplicationStatus[],
    },
    {
      title: "Entwurf",
      tone: "orange" as const,
      statuses: ["draft_open", "draft_approved"] as ApplicationStatus[],
    },
    {
      title: "Beworben",
      tone: "green" as const,
      statuses: ["gmail_draft_created", "applied", "follow_up_due"] as ApplicationStatus[],
    },
    {
      title: "Antwort",
      tone: "purple" as const,
      statuses: ["response_received", "interview", "rejected"] as ApplicationStatus[],
    },
  ];

  return groups.map((group) => {
    const items = applications.filter((application) =>
      group.statuses.includes(application.status),
    );
    return {
      title: group.title,
      tone: group.tone,
      count: items.length,
      cards: items.slice(0, 2).map((application) => ({
        id: application.id,
        title: application.job_detail.company,
        subtitle: application.job_detail.title,
        date: relativeDate(application.updated_at),
      })),
    };
  });
}

function buildTodayItems(
  applications: ApplicationDto[],
  mailMessages: EmailMessageDto[],
): TodayItem[] {
  const draftCount = countStatus(applications, ["draft_open", "draft_approved"]);
  const actionMailCount = mailMessages.filter((message) =>
    ["question", "invitation", "requires_action"].includes(message.classification),
  ).length;
  const followUpCount = applications.filter((application) =>
    isApplicationFollowUpDue(
      application,
      latestMailForApplication(application.id, mailMessages),
    ),
  ).length;
  return [
    {
      title: `${draftCount} Entwürfe prüfen & fertigstellen`,
      subtitle: "Bewerbungen abschließen",
      count: draftCount,
      icon: FileText,
      path: "/bewerbungen",
    },
    {
      title: `${actionMailCount} E-Mail beantworten`,
      subtitle: "Rückfragen und Einladungen prüfen",
      count: actionMailCount,
      icon: Mail,
      path: "/mail",
    },
    {
      title: `${followUpCount} Follow-ups verschicken`,
      subtitle: "Überfällige Follow-ups",
      count: followUpCount,
      icon: Bell,
      path: "/follow-ups",
    },
  ];
}

function countStatus(applications: ApplicationDto[], statuses: ApplicationStatus[]) {
  return applications.filter((application) => statuses.includes(application.status)).length;
}

function statusLabel(status: SearchCampaignDto["status"]) {
  const labels: Record<SearchCampaignDto["status"], string> = {
    draft: "Entwurf",
    active: "aktiv",
    paused: "pausiert",
    completed: "abgeschlossen",
  };
  return labels[status];
}

function remoteTypeLabel(value: string) {
  const normalized = value.toLowerCase();
  if (normalized === "remote") return "Remote";
  if (normalized === "hybrid") return "Hybrid";
  if (normalized === "onsite") return "Vor Ort";
  return value || "Unbekannt";
}

function manualJobPayload(form: ManualJobFormState): ManualJobPostingPayload {
  return {
    company: form.company.trim(),
    title: form.title.trim(),
    location: form.location.trim(),
    source: form.source.trim() || "Manuelle Eingabe",
    source_url: form.source_url.trim(),
    description: form.description.trim(),
    requirements: splitCsv(form.requirements),
    nice_to_have: splitCsv(form.nice_to_have),
    tags: splitCsv(form.tags),
    employment_type: form.employment_type.trim(),
    remote_type: form.remote_type.trim(),
  };
}

function readableError(error: unknown) {
  if (error instanceof ApiError) return error.message;
  if (error instanceof TypeError) {
    return "Keine Verbindung zum Backend möglich.";
  }
  if (error instanceof Error) return error.message;
  return "Unbekannter Fehler.";
}

function MailIcon({ size }: { size: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M4 6h16v12H4V6Zm0 1.5 8 5 8-5"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function BriefcaseIcon({ size = 24, strokeWidth = 2 }: { size?: number; strokeWidth?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M9 7V5.8C9 4.8 9.8 4 10.8 4h2.4c1 0 1.8.8 1.8 1.8V7m-9.2 3.4h12.4M5 7h14a2 2 0 0 1 2 2v8.5a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V9a2 2 0 0 1 2-2Z"
        stroke="currentColor"
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function BriefcaseGlyph() {
  return <BriefcaseIcon size={20} strokeWidth={2} />;
}

function GmailMark() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M4.5 7.5v9.25h15V7.5L12 13 4.5 7.5Z" fill="#fff" />
      <path d="M4.5 7.5 12 13l7.5-5.5" stroke="#ea4335" strokeWidth="2.4" strokeLinejoin="round" />
      <path d="M4.5 7.5v9.25" stroke="#34a853" strokeWidth="2.4" strokeLinecap="round" />
      <path d="M19.5 7.5v9.25" stroke="#4285f4" strokeWidth="2.4" strokeLinecap="round" />
      <path d="M4.5 16.75h15" stroke="#fbbc05" strokeWidth="2.4" strokeLinecap="round" />
    </svg>
  );
}
