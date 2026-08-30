"use client"

import { useMutation, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"
import { bulkNodeAction, nodeAction } from "../actions"
import { sessionKeys } from "../query"

function reportFailure(error: Error) {
  toast.error(error.message)
}

export function useNodeMutations(sessionId: string) {
  const queryClient = useQueryClient()
  const invalidateState = () =>
    queryClient.invalidateQueries({ queryKey: sessionKeys.state(sessionId) })

  const singleNodeMutation = useMutation({
    mutationFn: ({ nodeId, action }: { nodeId: string; action: string }) =>
      nodeAction(sessionId, nodeId, action),
    onSuccess: invalidateState,
    onError: reportFailure,
  })
  const bulkMutation = useMutation({
    mutationFn: (action: string) => bulkNodeAction(sessionId, action),
    onSuccess: invalidateState,
    onError: reportFailure,
  })

  return {
    nodeAction: (nodeId: string, action: string) =>
      singleNodeMutation.mutateAsync({ nodeId, action }),
    bulkNodeAction: (action: string) => bulkMutation.mutateAsync(action),
  }
}
