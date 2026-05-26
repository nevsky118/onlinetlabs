"use client"

import { type UIMessage, useChat } from "@ai-sdk/react"
import { useCallback, useState } from "react"

export function useChatStream(
  sessionId: string,
  initialMessages?: UIMessage[]
) {
  const [input, setInput] = useState("")

  const chat = useChat({
    id: sessionId,
    messages: initialMessages,
  })

  const handleSubmit = useCallback(
    (e?: React.FormEvent) => {
      e?.preventDefault()
      const text = input.trim()
      if (!text) return
      setInput("")
      chat.sendMessage({ text })
    },
    [input, chat]
  )

  return {
    messages: chat.messages,
    status: chat.status,
    stop: chat.stop,
    error: chat.error,
    setMessages: chat.setMessages,
    input,
    setInput,
    handleSubmit,
  }
}
