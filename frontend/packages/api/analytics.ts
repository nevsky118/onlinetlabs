type PropertyValue = string | number | boolean | null

export type EventMap = {
  page_view: { path: string; title?: string; referrer?: string }
  page_exit: { path: string; time_on_page_ms: number }
  session_launch_clicked: { lab_slug: string }
  session_launched: {
    lab_slug: string
    session_id: string
    provisioning_ms: number
  }
  session_launch_failed: { lab_slug: string; error: string }
  session_launch_denied: { lab_slug: string; code: string }
  session_queued: { lab_slug: string; position: number; eta_sec?: number }
  session_ended: { lab_slug: string; session_id: string; reason: string }
  session_reset: { lab_slug: string; session_id: string }
  step_viewed: { lab_slug: string; step_index: number; step_slug?: string }
  step_changed: { lab_slug: string; from_index: number; to_index: number }
  hint_requested: { lab_slug: string; step_index: number }
  credential_copied: { field: string }
  gns3_link_opened: { lab_slug: string; session_id?: string }
  node_action_triggered: {
    action: string
    session_id?: string
    node_id?: string
  }
  idle_start: { path: string; threshold_ms: number }
  idle_end: { path: string; idle_duration_ms: number }
  tab_hidden: { path: string }
  tab_visible: { path: string; hidden_duration_ms: number }
  chat_opened: { session_id: string; lab_slug?: string }
  chat_message_sent: {
    session_id: string
    lab_slug?: string
    message_length: number
  }
  chat_response_received: { session_id: string; lab_slug?: string }
  chat_history_viewed: { past_session_id: string }
  login_clicked: { method: string }
  login_success: { method: string }
  logout_clicked: Record<string, never>
}

type EventName = keyof EventMap

interface PendingEvent {
  event_name: string
  session_id?: string
  properties: Record<string, PropertyValue>
  client_ts: string
}

let _sessionId: string | null = null
let _labSlug: string | null = null
const _buffer: PendingEvent[] = []
let _flushTimer: ReturnType<typeof setInterval> | null = null
let _deviceIdCache: string | null = null

// Analytics base origin. Empty means same origin.
const _base = process.env.NEXT_PUBLIC_ANALYTICS_URL ?? ""

export function setAnalyticsContext(
  sessionId: string | null,
  labSlug: string | null
): void {
  _sessionId = sessionId
  _labSlug = labSlug
}

function getDeviceId(): string {
  if (typeof window === "undefined") return "server"
  if (_deviceIdCache) return _deviceIdCache
  let id = localStorage.getItem("otl_device_id")
  if (!id) {
    id = crypto.randomUUID()
    localStorage.setItem("otl_device_id", id)
  }
  _deviceIdCache = id
  return id
}

// Typed core. Events from EventMap are checked at compile time so that names
// and shapes do not drift apart and fragment the dataset
export function track<K extends EventName>(
  name: K,
  properties: EventMap[K]
): void {
  enqueue(name, properties as Record<string, PropertyValue>)
}

// Fallback path for arbitrary frontend events (as in Vercel), without shape checking.
// Suitable for experimental or one-off events that do not need an EventMap entry
export function trackCustom(
  name: string,
  properties: Record<string, PropertyValue> = {}
): void {
  enqueue(name, properties)
}

function enqueue(
  name: string,
  properties: Record<string, PropertyValue>
): void {
  if (typeof window === "undefined") return

  // session_id is an indexed join key, taken from the explicit property, otherwise from the context
  const { session_id, ...rest } = properties
  const resolvedSession =
    (session_id as string | undefined) ?? _sessionId ?? undefined

  _buffer.push({
    event_name: name,
    session_id: resolvedSession,
    properties: {
      ...rest,
      // context and auto-captured fields go into the shared properties
      ...(_labSlug && !("lab_slug" in rest) ? { lab_slug: _labSlug } : {}),
      page: window.location.pathname,
      user_agent: navigator.userAgent,
    },
    client_ts: new Date().toISOString(),
  })

  if (_buffer.length >= 10) void flush()
}

async function flush(): Promise<void> {
  if (_buffer.length === 0) return
  const batch = _buffer.splice(0, 50)
  try {
    await fetch(`${_base}/api/analytics`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ device_id: getDeviceId(), events: batch }),
      credentials: "include",
      keepalive: true,
    })
  } catch {
    // swallow the error, analytics must not break the UX
  }
}

function flushBeacon(): void {
  if (_buffer.length === 0) return
  const batch = _buffer.splice(0)
  navigator.sendBeacon(
    `${_base}/api/analytics`,
    new Blob([JSON.stringify({ device_id: getDeviceId(), events: batch })], {
      type: "application/json",
    })
  )
}

export function initAnalytics(): () => void {
  if (_flushTimer) clearInterval(_flushTimer)
  _flushTimer = setInterval(() => void flush(), 5000)
  window.addEventListener("beforeunload", flushBeacon)
  return () => {
    if (_flushTimer) clearInterval(_flushTimer)
    window.removeEventListener("beforeunload", flushBeacon)
  }
}
