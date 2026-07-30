// t is useTranslations("dashboard.session.eventLabels"), resolved in the component, not at module level
const EVENT_LABEL_KEYS: Record<string, string> = {
  "node.started": "nodeStarted",
  "node.stopped": "nodeStopped",
  "node.suspended": "nodeSuspended",
  "node.reloaded": "nodeReloaded",
  "node.console_opened": "consoleOpened",
  "link.created": "linkCreated",
  "link.deleted": "linkDeleted",
  "session.started": "sessionStarted",
  "session.ended": "sessionEnded",
}

export function labelForEvent(
  eventType: string,
  t: (key: string) => string
): string {
  const key = EVENT_LABEL_KEYS[eventType]
  return key ? t(key) : eventType
}
