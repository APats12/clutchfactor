import { useQuery } from '@tanstack/react-query'
import { fetchPlays } from '../api/games'
import type { Play } from '../types/play'

export function usePlays(gameId: string | undefined) {
  return useQuery<Play[]>({
    queryKey: ['plays', gameId],
    queryFn: () => fetchPlays(gameId!),
    enabled: !!gameId,
    staleTime: 5_000,
  })
}
