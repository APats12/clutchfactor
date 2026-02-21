import { useQuery } from '@tanstack/react-query'
import { fetchGames } from '../api/games'
import type { Game } from '../types/game'

export function useGames(params?: { date?: string; status?: string; season?: number; week?: number; playoffs?: boolean }) {
  return useQuery<Game[]>({
    queryKey: ['games', params],
    queryFn: () => fetchGames(params),
    staleTime: 30_000,
    refetchInterval: 60_000,
  })
}
