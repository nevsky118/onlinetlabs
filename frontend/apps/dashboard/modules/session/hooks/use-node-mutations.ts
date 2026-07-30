"use client"

import { useMutation, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"
import { bulkNodeAction, nodeAction } from "../actions"
import { sessionKeys } from "../query"

export function useNodeMutations(sessionId: string) {
  const qc = useQueryClient()
  const invalidate = () =>
    qc.invalidateQueries({ queryKey: sessionKeys.state(sessionId) })
  const onError = (e: unknown) => toast.error((e as Error).message)

  const node = useMutation({
    mutationFn: ({ nodeId, action }: { nodeId: string; action: string }) =>
      nodeAction(sessionId, nodeId, action),
    onSuccess: invalidate,
    onError,
  })
  const bulk = useMutation({
    mutationFn: (action: string) => bulkNodeAction(sessionId, action),
    onSuccess: invalidate,
    onError,
  })

  return {
    nodeAction: (nodeId: string, action: string) =>
      node.mutateAsync({ nodeId, action }),
    bulkNodeAction: (action: string) => bulk.mutateAsync(action),
  }
}
