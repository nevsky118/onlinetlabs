"use client"

import { usePathname } from "next/navigation"
import { useEffect, useRef } from "react"
import { initAnalytics, track } from "@/lib/analytics"

const IDLE_MS = 60_000
const ACTIVITY = [
  "mousemove",
  "keydown",
  "click",
  "scroll",
  "touchstart",
] as const

export function AnalyticsProvider({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const prevPath = useRef<string | null>(null)
  const pageEntry = useRef(Date.now())
  const idleTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const isIdle = useRef(false)
  const idleStartedAt = useRef<number | null>(null)
  const hiddenAt = useRef<number | null>(null)

  useEffect(() => initAnalytics(), [])

  useEffect(() => {
    if (prevPath.current && prevPath.current !== pathname) {
      track("page_exit", {
        path: prevPath.current,
        time_on_page_ms: Date.now() - pageEntry.current,
      })
    }
    track("page_view", {
      path: pathname,
      title: document.title,
      referrer: document.referrer || undefined,
    })
    prevPath.current = pathname
    pageEntry.current = Date.now()
  }, [pathname])

  useEffect(() => {
    function resetIdle() {
      if (isIdle.current) {
        track("idle_end", {
          path: window.location.pathname,
          idle_duration_ms: idleStartedAt.current
            ? Date.now() - idleStartedAt.current
            : IDLE_MS,
        })
        isIdle.current = false
        idleStartedAt.current = null
      }
      if (idleTimer.current) clearTimeout(idleTimer.current)
      idleTimer.current = setTimeout(() => {
        isIdle.current = true
        idleStartedAt.current = Date.now()
        track("idle_start", {
          path: window.location.pathname,
          threshold_ms: IDLE_MS,
        })
      }, IDLE_MS)
    }
    ACTIVITY.forEach((e) => {
      window.addEventListener(e, resetIdle, { passive: true })
    })
    resetIdle()
    return () => {
      ACTIVITY.forEach((e) => {
        window.removeEventListener(e, resetIdle)
      })
      if (idleTimer.current) clearTimeout(idleTimer.current)
    }
  }, [])

  useEffect(() => {
    function onVisibility() {
      if (document.hidden) {
        hiddenAt.current = Date.now()
        track("tab_hidden", { path: window.location.pathname })
      } else {
        track("tab_visible", {
          path: window.location.pathname,
          hidden_duration_ms: hiddenAt.current
            ? Date.now() - hiddenAt.current
            : 0,
        })
        hiddenAt.current = null
      }
    }
    document.addEventListener("visibilitychange", onVisibility)
    return () => document.removeEventListener("visibilitychange", onVisibility)
  }, [])

  return <>{children}</>
}
