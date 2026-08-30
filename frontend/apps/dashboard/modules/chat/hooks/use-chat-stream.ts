"use client"

import { type UIMessage, useChat } from "@ai-sdk/react"
import { useCallback, useState } from "react"

export function useChatStream(
  sessionId: string,
  modelId?: string,
  initialMessages?: UIMessage[]
) {
  const [input, setInput] = useState("")

  const chat = useChat({
    id: sessionId,
    messages: initialMessages,
  })

  const handleSubmit = useCallback(
    (event?: React.FormEvent) => {
      event?.preventDefault()
      const text = input.trim()
      if (!text) return
      setInput("")
      chat.sendMessage(
        { text },
        modelId ? { body: { model_id: modelId } } : undefined
      )
    },
    [input, chat, modelId]
  )

  const sendText = useCallback(
    (text: string) => {
      const trimmed = text.trim()
      if (!trimmed) return
      chat.sendMessage(
        { text: trimmed },
        modelId ? { body: { model_id: modelId } } : undefined
      )
    },
    [chat, modelId]
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
    sendText,
  }
}
