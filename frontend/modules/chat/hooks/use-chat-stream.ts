"use client"

import { type UIMessage, useChat } from "@ai-sdk/react"
import { useCallback, useRef, useState } from "react"

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

  // ref чтобы замыкания handleSubmit/sendText видели актуальный modelId
  const modelRef = useRef(modelId)
  modelRef.current = modelId

  const handleSubmit = useCallback(
    (e?: React.FormEvent) => {
      e?.preventDefault()
      const text = input.trim()
      if (!text) return
      setInput("")
      chat.sendMessage(
        { text },
        modelRef.current ? { body: { model_id: modelRef.current } } : undefined
      )
    },
    [input, chat]
  )

  const sendText = useCallback(
    (text: string) => {
      const trimmed = text.trim()
      if (!trimmed) return
      chat.sendMessage(
        { text: trimmed },
        modelRef.current ? { body: { model_id: modelRef.current } } : undefined
      )
    },
    [chat]
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
