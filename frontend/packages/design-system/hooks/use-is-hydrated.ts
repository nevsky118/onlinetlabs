"use client"

import { useSyncExternalStore } from "react"

const subscribe = () => () => {}
const getSnapshot = () => true
const getServerSnapshot = () => false

/**
 * False on the server and through the hydration render, true afterwards.
 * Lets a component defer browser-only values without setting state in an effect.
 */
export function useIsHydrated(): boolean {
  return useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot)
}
