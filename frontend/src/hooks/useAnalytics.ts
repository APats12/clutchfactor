import { useQuery } from '@tanstack/react-query'
import {
  fetchMomentumSwings,
  fetchClutchIndex,
  fetchDecisionGrades,
} from '../api/games'
import type {
  MomentumSwingsResponse,
  ClutchResponse,
  DecisionGradesResponse,
} from '../types/analytics'

export function useMomentumSwings(gameId: string | undefined, hasPlays: boolean) {
  return useQuery<MomentumSwingsResponse>({
    queryKey: ['momentumSwings', gameId],
    queryFn: () => fetchMomentumSwings(gameId!),
    enabled: !!gameId && hasPlays,
    staleTime: 60_000,
  })
}

export function useClutchIndex(gameId: string | undefined, hasPlays: boolean) {
  return useQuery<ClutchResponse>({
    queryKey: ['clutchIndex', gameId],
    queryFn: () => fetchClutchIndex(gameId!),
    enabled: !!gameId && hasPlays,
    staleTime: 60_000,
  })
}

export function useDecisionGrades(gameId: string | undefined, hasPlays: boolean) {
  return useQuery<DecisionGradesResponse>({
    queryKey: ['decisionGrades', gameId],
    queryFn: () => fetchDecisionGrades(gameId!),
    enabled: !!gameId && hasPlays,
    staleTime: 60_000,
  })
}
