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

export interface LogTable {
  slug: string
  label: string
  icon: LucideIcon
  group: string
}

export const LOG_TABLES: LogTable[] = [
  { slug: "mcp_audit", label: "MCP-аудит", icon: Activity, group: "Логи" },
  {
    slug: "agent_activity_events",
    label: "Активность агентов",
    icon: Bell,
    group: "Логи",
  },
  {
    slug: "platform_events",
    label: "События платформы",
    icon: FileText,
    group: "Логи",
  },
  {
    slug: "behavioral_events",
    label: "Поведение",
    icon: MousePointer,
    group: "Логи",
  },
  {
    slug: "chat_messages",
    label: "Сообщения чата",
    icon: MessageSquare,
    group: "Логи",
  },
  {
    slug: "learning_sessions",
    label: "Сессии обучения",
    icon: BookOpen,
    group: "Сессии",
  },
  {
    slug: "validation_runs",
    label: "Прогоны валидации",
    icon: CheckCircle,
    group: "Сессии",
  },
  {
    slug: "process_state_samples",
    label: "Состояния процесса",
    icon: Cpu,
    group: "Сессии",
  },
  {
    slug: "lab_progress",
    label: "Прогресс по лабам",
    icon: FlaskConical,
    group: "Прогресс",
  },
  {
    slug: "course_progress",
    label: "Прогресс по курсам",
    icon: GraduationCap,
    group: "Прогресс",
  },
  {
    slug: "step_attempts",
    label: "Попытки шагов",
    icon: Target,
    group: "Прогресс",
  },
  {
    slug: "experiment_metrics",
    label: "Метрики эксперимента",
    icon: BarChart2,
    group: "Прогресс",
  },
  { slug: "consents", label: "Согласия", icon: ShieldCheck, group: "Доступ" },
]

export function getLogTable(slug: string): LogTable | undefined {
  return LOG_TABLES.find((t) => t.slug === slug)
}
