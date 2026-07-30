import {
  Activity,
  BarChart2,
  Bell,
  BookOpen,
  CheckCircle,
  Cpu,
  FileText,
  FlaskConical,
  GraduationCap,
  type LucideIcon,
  MessageSquare,
  MousePointer,
  ShieldCheck,
  Target,
} from "lucide-react"

export type LogGroup = "logs" | "sessions" | "progress" | "access"

export interface LogTable {
  slug: string
  icon: LucideIcon
  group: LogGroup
}

// group is a stable id for grouping in admin-nav. The display name is translated there
export const LOG_TABLES: LogTable[] = [
  { slug: "mcp_audit", icon: Activity, group: "logs" },
  { slug: "agent_activity_events", icon: Bell, group: "logs" },
  { slug: "platform_events", icon: FileText, group: "logs" },
  { slug: "behavioral_events", icon: MousePointer, group: "logs" },
  { slug: "chat_messages", icon: MessageSquare, group: "logs" },
  { slug: "learning_sessions", icon: BookOpen, group: "sessions" },
  { slug: "validation_runs", icon: CheckCircle, group: "sessions" },
  { slug: "process_state_samples", icon: Cpu, group: "sessions" },
  { slug: "lab_progress", icon: FlaskConical, group: "progress" },
  { slug: "course_progress", icon: GraduationCap, group: "progress" },
  { slug: "step_attempts", icon: Target, group: "progress" },
  { slug: "experiment_metrics", icon: BarChart2, group: "progress" },
  { slug: "consents", icon: ShieldCheck, group: "access" },
]

export function getLogTable(slug: string): LogTable | undefined {
  return LOG_TABLES.find((t) => t.slug === slug)
}

// t is useTranslations/getTranslations("dashboard.admin.logTables"). Keys are slugs in camelCase
const LABEL_KEYS: Record<string, string> = {
  mcp_audit: "mcpAudit",
  agent_activity_events: "agentActivityEvents",
  platform_events: "platformEvents",
  behavioral_events: "behavioralEvents",
  chat_messages: "chatMessages",
  learning_sessions: "learningSessions",
  validation_runs: "validationRuns",
  process_state_samples: "processStateSamples",
  lab_progress: "labProgress",
  course_progress: "courseProgress",
  step_attempts: "stepAttempts",
  experiment_metrics: "experimentMetrics",
  consents: "consents",
}

export function getLogTableLabel(
  t: (key: string) => string,
  slug: string
): string {
  return t(LABEL_KEYS[slug] ?? slug)
}
