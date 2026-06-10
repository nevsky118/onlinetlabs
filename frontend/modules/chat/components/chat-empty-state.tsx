"use client"

import {
  CompassIcon,
  LightbulbIcon,
  NetworkIcon,
  WrenchIcon,
} from "lucide-react"
import { cn } from "@/lib/utils"

const SUGGESTIONS = [
  {
    icon: NetworkIcon,
    title: "Топология лабы",
    description: "Объясни, как устроена схема",
    prompt: "Объясни топологию этой лабораторной работы.",
  },
  {
    icon: CompassIcon,
    title: "С чего начать",
    description: "Помоги сделать первый шаг",
    prompt: "С чего мне начать выполнение этого задания?",
  },
  {
    icon: WrenchIcon,
    title: "Настройка узла",
    description: "Разбери команды по шагам",
    prompt: "Как настроить интерфейсы на узлах в этой лабе?",
  },
  {
    icon: LightbulbIcon,
    title: "Подсказка",
    description: "Подтолкни, не раскрывая ответ",
    prompt: "Дай подсказку к текущему заданию, не раскрывая решение целиком.",
  },
]

function getGreeting(): string {
  const h = new Date().getHours()
  if (h >= 5 && h < 12) return "Доброе утро."
  if (h >= 12 && h < 18) return "Добрый день."
  return "Добрый вечер."
}

export function ChatSuggestions({
  onSuggestion,
  horizontal,
}: {
  onSuggestion: (prompt: string) => void
  // Карточки в ряд для полноэкранного режима, как на CF /sphere
  horizontal?: boolean
}) {
  return (
    <div
      className={cn(
        "flex gap-2",
        horizontal
          ? "w-full flex-col flex-wrap items-center justify-center sm:flex-row"
          : "w-full max-w-72 flex-col"
      )}
    >
      {SUGGESTIONS.map((s, i) => (
        <button
          key={s.title}
          type="button"
          onClick={() => onSuggestion(s.prompt)}
          className={cn(
            "group bg-card hover:bg-background hover:border-primary/40 animate-in fade-in-0 slide-in-from-bottom-2 relative z-10 flex cursor-pointer items-center gap-3 border p-2 text-left fill-mode-both duration-300 [transition:border-color_200ms,background-color_200ms,box-shadow_200ms]",
            horizontal ? "w-full sm:w-auto" : "w-full"
          )}
          style={{ animationDelay: `${i * 60}ms` }}
        >
          <div className="bg-primary group-hover:h-5 absolute top-1/2 left-0 h-0 w-[2px] -translate-y-1/2 transition-all duration-200" />
          <div className="bg-muted group-hover:bg-primary/10 flex size-8 shrink-0 items-center justify-center transition-colors duration-200">
            <s.icon className="text-muted-foreground group-hover:text-primary size-3.5 transition-colors duration-200" />
          </div>
          <div className="flex min-w-0 flex-col">
            <span className="text-muted-foreground group-hover:text-foreground truncate text-xs font-medium">
              {s.title}
            </span>
            <span className="text-muted-foreground truncate text-xs">
              {s.description}
            </span>
          </div>
          <svg
            width="12"
            height="12"
            viewBox="0 0 12 12"
            fill="none"
            aria-hidden="true"
            className="text-primary ml-auto shrink-0 opacity-0 transition-opacity duration-200 group-hover:opacity-100"
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
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-8 overflow-y-auto p-4">
      <div className="text-center">
        <h3 className="text-foreground mb-1.5 text-lg font-medium">
          {getGreeting()}
        </h3>
        <p className="text-muted-foreground text-sm">Чем займёмся сегодня?</p>
      </div>
      <ChatSuggestions onSuggestion={onSuggestion} />
    </div>
  )
}
