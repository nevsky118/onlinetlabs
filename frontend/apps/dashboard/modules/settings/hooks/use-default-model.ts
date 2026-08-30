"use client"

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import type { ModelOption } from "../types"
import { saveDefaultModelId } from "../api"
import { chatModelsQuery, defaultModelQuery, settingsKeys } from "../query"

const NO_MODELS: ModelOption[] = []

/** The model list plus the student's saved default, with an optimistic save. */
export function useDefaultModel(onSaveFailed: () => void) {
  const queryClient = useQueryClient()
  const { data: models, isError: modelsFailed } = useQuery(chatModelsQuery())
  const { data: savedModelId } = useQuery(defaultModelQuery())

  const saveMutation = useMutation({
    mutationFn: saveDefaultModelId,
    onSuccess: (_result, modelId) => {
      queryClient.setQueryData(settingsKeys.defaultModel(), modelId)
    },
    onError: onSaveFailed,
  })

  return {
    // A failed list reads as "no models", which the view renders as unavailable.
    models: models ?? (modelsFailed ? NO_MODELS : null),
    // While a save is in flight the picked value wins, so the select does not
    // snap back to the stored one.
    selectedModelId: saveMutation.isPending
      ? saveMutation.variables
      : (savedModelId ?? null),
    save: saveMutation.mutate,
    isSaving: saveMutation.isPending,
  }
}
