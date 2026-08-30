import { Badge } from "@repo/design-system/ui/badge"
import { Link } from "@repo/i18n/navigation"
import { BanIcon, ChevronLeftIcon } from "lucide-react"
import { useTranslations } from "next-intl"
import type { SessionStatus } from "../types"

const STATUS_VARIANT: Record<
  SessionStatus,
  "default" | "secondary" | "outline" | "destructive"
> = {
  provisioning: "secondary",
  active: "default",
  ended: "outline",
  error: "destructive",
}

export function SessionPageHeader({
  lab,
  status,
  noAssist,
}: {
  lab: { slug: string; title: string | null }
  status: SessionStatus
  noAssist: boolean
}) {
  const t = useTranslations("dashboard.session.pageHeader")
  return (
    <div className="flex min-w-0 items-center gap-2 text-sm">
      {/* Back to labs: icon-only on mobile, icon+label on desktop. */}
      <Link
        href="/labs"
        className="inline-flex shrink-0 items-center gap-1 text-muted-foreground hover:text-foreground"
        aria-label={t("backToLabs")}
      >
        <ChevronLeftIcon className="size-4" />
        <span className="hidden sm:inline">{t("labs")}</span>
      </Link>
      <span className="hidden text-muted-foreground sm:inline">/</span>
      {/* Title: truncate to one line, keep status badge inline. */}
      <Link
        href={`/labs/${lab.slug}`}
        className="min-w-0 truncate font-medium hover:underline"
      >
        {lab.title ?? lab.slug}
      </Link>
      <Badge variant={STATUS_VARIANT[status]} className="shrink-0 rounded-none">
        {status === "active" && (
          <span className="mr-1.5 inline-block size-2 rounded-full bg-current" />
        )}
        {t(`status.${status}`)}
      </Badge>
      {noAssist && (
        <Badge
          variant="default"
          className="shrink-0 tracking-wide uppercase"
          title={t("noAssistTitle")}
        >
          <BanIcon data-icon="inline-start" />
          {t("noAssist")}
        </Badge>
      )}
    </div>
  )
}
