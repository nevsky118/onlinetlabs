"use client"

import { ArrowUpIcon, SquareIcon } from "lucide-react"
import {
  InputGroup,
  InputGroupAddon,
  InputGroupButton,
  InputGroupTextarea,
} from "@/ui/input-group"
import { Tooltip, TooltipContent, TooltipTrigger } from "@/ui/tooltip"

type Props = {
  input: string
  setInput: (v: string) => void
  handleSubmit: (e: React.FormEvent) => void
  status: string
  stop?: () => void
}

export function ChatInput({
  input,
  setInput,
  handleSubmit,
  status,
  stop,
}: Props) {
  const isStreaming = status === "streaming" || status === "submitted"

  return (
    <form className="p-3" onSubmit={handleSubmit}>
      <InputGroup>
        <InputGroupTextarea
          placeholder="Спросите тьютора..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault()
              if (input.trim() && !isStreaming)
                e.currentTarget.form?.requestSubmit()
            }
          }}
        />
        <InputGroupAddon align="block-end">
          {isStreaming && stop ? (
            <Tooltip>
              <TooltipTrigger asChild>
                <InputGroupButton
                  type="button"
                  aria-label="Остановить"
                  variant="destructive"
                  size="icon-sm"
                  className="ml-auto rounded-full"
                  onClick={stop}
                >
                  <SquareIcon />
                </InputGroupButton>
              </TooltipTrigger>
              <TooltipContent>Остановить генерацию</TooltipContent>
            </Tooltip>
          ) : (
            <InputGroupButton
              type="submit"
              aria-label="Отправить"
              size="icon-sm"
              className="ml-auto rounded-full"
              disabled={!input.trim() || isStreaming}
            >
              <ArrowUpIcon />
            </InputGroupButton>
          )}
        </InputGroupAddon>
      </InputGroup>
    </form>
  )
}
