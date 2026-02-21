import { useQuery } from '@tanstack/react-query'
import { fetchGame } from '../api/games'
import type { GameDetail } from '../types/game'

export function useGame(id: string | undefined) {
  return useQuery<GameDetail>({
    queryKey: ['game', id],
    queryFn: () => fetchGame(id!),
    enabled: !!id,
    staleTime: 15_000,
  })
}
