"use client"

import { type ComponentProps, memo } from "react"
import { Streamdown } from "streamdown"
import { cn } from "@/lib/utils"

type ResponseProps = ComponentProps<typeof Streamdown>

export const ChatResponse = memo(
  ({ className, ...props }: ResponseProps) => (
    <Streamdown
      className={cn(
        "size-full [&>*:first-child]:mt-0 [&>*:last-child]:mb-0",
        // Списки: единый отступ маркеров, чтобы пункты не уезжали из колонки текста.
        "[&_ol]:my-2 [&_ol]:list-decimal [&_ol]:pl-5 [&_ul]:my-2 [&_ul]:list-disc [&_ul]:pl-5 [&_li]:my-1 [&_li]:marker:text-muted-foreground",
        className
      )}
      {...props}
    />
  ),
  (prev, next) => prev.children === next.children
)

ChatResponse.displayName = "ChatResponse"
