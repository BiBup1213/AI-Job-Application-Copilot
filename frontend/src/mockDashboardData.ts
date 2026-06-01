import {
  Bell,
  BriefcaseBusiness,
  CheckCircle2,
  Clock3,
  FileText,
  Inbox,
  Mail,
  Search,
  type LucideIcon,
} from "lucide-react";

export type StatusTone = "blue" | "green" | "orange" | "red" | "gray";

export type Job = {
  id: string;
  apiId?: number;
  applicationId?: number;
  logo: string;
  company: string;
  title: string;
  location: string;
  mode: string;
  published?: string;
  tags: string[];
  score: number;
  status: string;
  statusTone: StatusTone;
  nextAction: string;
  strengths: string[];
  risks: string[];
  angle: string;
  sourceUrl?: string;
};

export type Kpi = {
  label: string;
  value: string;
  subtitle: string;
  icon: LucideIcon;
};

export const navigationItems = [
  { label: "Übersicht", icon: BriefcaseBusiness, path: "/" },
  { label: "Suchkampagnen", icon: Search, path: "/suchkampagnen" },
  { label: "Gefundene Jobs", icon: Inbox, path: "/jobs" },
  { label: "Bewerbungen", icon: FileText, path: "/bewerbungen" },
  { label: "Mail-Zentrale", icon: Mail, path: "/mail" },
  { label: "Follow-ups", icon: Bell, path: "/follow-ups" },
  { label: "Profil", icon: CheckCircle2, path: "/profil" },
  { label: "Einstellungen", icon: Clock3, path: "/einstellungen" },
];
