"use client"

import { cn } from "@repo/design-system/lib/utils"
import {
  CompassIcon,
  LightbulbIcon,
  NetworkIcon,
  WrenchIcon,
} from "lucide-react"
import { useTranslations } from "next-intl"

// Built per call because the suggestions come from the active translations
function getSuggestions(t: (key: string) => string) {
  return [
    {
      icon: NetworkIcon,
      title: t("topology.title"),
      description: t("topology.description"),
      prompt: t("topology.prompt"),
    },
    {
      icon: CompassIcon,
      title: t("gettingStarted.title"),
      description: t("gettingStarted.description"),
      prompt: t("gettingStarted.prompt"),
    },
    {
      icon: WrenchIcon,
      title: t("nodeSetup.title"),
      description: t("nodeSetup.description"),
      prompt: t("nodeSetup.prompt"),
    },
    {
      icon: LightbulbIcon,
      title: t("hint.title"),
      description: t("hint.description"),
      prompt: t("hint.prompt"),
    },
  ]
}

function getGreeting(t: (key: string) => string): string {
  const hour = new Date().getHours()
  if (hour >= 5 && hour < 12) return t("morning")
  if (hour >= 12 && hour < 18) return t("afternoon")
  return t("evening")
}

export function ChatSuggestions({
  onSuggestion,
  horizontal,
}: {
  onSuggestion: (prompt: string) => void
  // Cards in a row for fullscreen mode, like on CF /sphere
  horizontal?: boolean
}) {
  const t = useTranslations("dashboard.chat.suggestions")
  const suggestions = getSuggestions(t)
  return (
    <div
      className={cn(
        "flex gap-2",
        horizontal
          ? "w-full flex-col flex-wrap items-center justify-center sm:flex-row"
          : "w-full max-w-72 flex-col"
      )}
    >
      {suggestions.map((suggestion, index) => (
        <button
          key={suggestion.title}
          type="button"
          onClick={() => onSuggestion(suggestion.prompt)}
          className={cn(
            "group relative z-10 flex animate-in cursor-pointer items-center gap-3 border bg-card p-2 text-left duration-300 fade-in-0 fill-mode-both [transition:border-color_200ms,background-color_200ms,box-shadow_200ms] slide-in-from-bottom-2 hover:border-primary/40 hover:bg-background",
            horizontal ? "w-full sm:w-auto" : "w-full"
          )}
          style={{ animationDelay: `${index * 60}ms` }}
        >
          <div className="absolute top-1/2 left-0 h-0 w-[2px] -translate-y-1/2 bg-primary transition-all duration-200 group-hover:h-5" />
          <div className="flex size-8 shrink-0 items-center justify-center bg-muted transition-colors duration-200 group-hover:bg-primary/10">
            <suggestion.icon className="size-3.5 text-muted-foreground transition-colors duration-200 group-hover:text-primary" />
          </div>
          <div className="flex min-w-0 flex-col">
            <span className="truncate text-xs font-medium text-muted-foreground group-hover:text-foreground">
              {suggestion.title}
            </span>
            <span className="truncate text-xs text-muted-foreground">
              {suggestion.description}
            </span>
          </div>
          <svg
            width="12"
            height="12"
            viewBox="0 0 12 12"
            fill="none"
            aria-hidden="true"
            className="ml-auto shrink-0 text-primary opacity-0 transition-opacity duration-200 group-hover:opacity-100"
          >
            <path
              d="M4.5 2.5L8 6L4.5 9.5"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </button>
      ))}
    </div>
  )
}

export function ChatEmptyState({
  onSuggestion,
}: {
  onSuggestion: (prompt: string) => void
}) {
  const t = useTranslations("dashboard.chat.emptyState")
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-8 overflow-y-auto p-4">
      <div className="text-center">
        <h3 className="mb-1.5 text-lg font-medium text-foreground">
          {getGreeting(t)}
        </h3>
        <p className="text-sm text-muted-foreground">{t("prompt")}</p>
      </div>
      <ChatSuggestions onSuggestion={onSuggestion} />
    </div>
  )
}
