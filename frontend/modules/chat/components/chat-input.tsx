"use client"

import { ArrowUpIcon, SquareIcon } from "lucide-react"
import { cn } from "@/lib/utils"
import { Badge } from "@/ui/badge"
import { Button } from "@/ui/button"
import { Tooltip, TooltipContent, TooltipTrigger } from "@/ui/tooltip"

type Props = {
  input: string
  setInput: (v: string) => void
  handleSubmit: (e: React.FormEvent) => void
  status: string
  stop?: () => void
  // Крупная форма для полноэкранного режима, как на CF /sphere
  large?: boolean
  className?: string
  // Слот выбора модели — в композере рядом с подписью агента (как в claude.ai).
  modelSelector?: React.ReactNode
}

export function ChatInput({
  input,
  setInput,
  handleSubmit,
  status,
  stop,
  large,
  className,
  modelSelector,
}: Props) {
  const isStreaming = status === "streaming" || status === "submitted"

  return (
    <form className={cn("p-4 pt-2", className)} onSubmit={handleSubmit}>
      <div className="bg-background focus-within:border-primary/50 focus-within:ring-primary/50 flex w-full flex-col gap-2 border transition-all focus-within:ring-1">
        <textarea
          rows={2}
          placeholder={large ? "Спросите о чём угодно..." : "Чем можем помочь?"}
          name="promptInput"
          value={input}
          className={cn(
            "text-foreground placeholder:text-muted-foreground max-h-64 w-full resize-none overflow-y-auto bg-transparent outline-none",
            large ? "p-5 pb-0 text-base" : "p-3 pb-0 text-sm"
          )}
          onChange={(e) => {
            setInput(e.target.value)
            e.target.style.height = "auto"
            e.target.style.height = `${e.target.scrollHeight}px`
          }}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault()
              if (input.trim() && !isStreaming)
                e.currentTarget.form?.requestSubmit()
            }
          }}
        />
        <div
          className={cn(
            "flex cursor-text items-center justify-between gap-1 pt-0",
            large ? "p-3" : "p-2"
          )}
        >
          <div className="flex min-w-0 items-center gap-1.5">
            <Badge variant="secondary" className="text-muted-foreground">
              TutorAgent
            </Badge>
            {modelSelector}
          </div>
          {isStreaming && stop ? (
            <Tooltip>
              <TooltipTrigger
                render={
                  <Button
                    type="button"
                    aria-label="Остановить генерацию"
                    variant="destructive"
                    size={large ? "icon" : "icon-sm"}
                    onClick={stop}
                  />
                }
              >
                <SquareIcon />
              </TooltipTrigger>
              <TooltipContent>Остановить генерацию</TooltipContent>
            </Tooltip>
          ) : (
            <Button
              type="submit"
              aria-label="Отправить"
              size={large ? "icon" : "icon-sm"}
              disabled={!input.trim() || isStreaming}
            >
              <ArrowUpIcon />
            </Button>
          )}
        </div>
      </div>
    </form>
  )
}
