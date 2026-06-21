// Чат как переиспользуемые примитивы (flat, shadcn-style). Конфиг сессии
// прокидывается один раз в ChatProvider, остальное берётся из контекста:
//   <ChatProvider sessionId labSlug canViewLogs>
//     <ChatInset>{page}</ChatInset>
//     <ChatTrigger />
//     <ChatPanel />
//   </ChatProvider>

export type { ChatConfig } from "./components/chat-panel-provider"
export type { AgentActivityEvent } from "./types"
export { ChatMessages } from "./components/chat-messages"
export { ChatPanel } from "./components/chat-panel"
export {
  ChatInset,
  ChatProvider,
  ChatTrigger,
} from "./components/chat-panel-provider"
export { ChatResponse } from "./components/chat-response"
export { Conversation } from "./components/conversation"
export { ChatView } from "./views/chat-view"
