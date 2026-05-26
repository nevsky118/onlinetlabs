export const EVENT_LABEL: Record<string, string> = {
  "node.started": "Узел запущен",
  "node.stopped": "Узел остановлен",
  "node.suspended": "Узел приостановлен",
  "node.reloaded": "Узел перезагружен",
  "node.console_opened": "Открыта консоль",
  "link.created": "Создан линк",
  "link.deleted": "Удалён линк",
  "session.started": "Сессия запущена",
  "session.ended": "Сессия завершена",
}

export function labelForEvent(eventType: string): string {
  return EVENT_LABEL[eventType] ?? eventType
}
