import type { Game } from '../../types/game'
import { GameCard } from './GameCard'

interface GamesListProps {
  games: Game[]
}

export function GamesList({ games }: GamesListProps) {
  if (games.length === 0) {
    return (
      <p className="py-12 text-center text-gray-500">
        No games found for the selected filters.
      </p>
    )
  }

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
      {games.map((game) => (
        <GameCard key={game.id} game={game} />
      ))}
    </div>
  )
}
