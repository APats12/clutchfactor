import { Link } from 'react-router-dom'
import type { Game } from '../../types/game'
import { StatusBadge } from '../common/Badge'

interface GameCardProps {
  game: Game
}

function WpBar({ homeWp, homeColor, awayColor }: { homeWp: number; homeColor: string; awayColor: string }) {
  const homePct = Math.round(homeWp * 100)
  return (
    <div className="mt-2 overflow-hidden rounded-full">
      <div className="flex h-2 w-full">
        <div
          style={{ width: `${homePct}%`, backgroundColor: homeColor || '#C60C30' }}
          className="transition-all duration-700"
        />
        <div
          style={{ width: `${100 - homePct}%`, backgroundColor: awayColor || '#A5ACAF' }}
          className="transition-all duration-700"
        />
      </div>
      <div className="mt-1 flex justify-between text-xs text-gray-500">
        <span>{homePct}%</span>
        <span>{100 - homePct}%</span>
      </div>
    </div>
  )
}

export function GameCard({ game }: GameCardProps) {
  const { home_team: home, away_team: away } = game

  return (
    <Link
      to={`/games/${game.id}`}
      className="block rounded-xl border border-gray-200 bg-white p-4 shadow-sm transition-all duration-200 hover:shadow-lg hover:scale-[1.01]"
    >
      <div className="mb-2 flex items-center justify-between">
        <StatusBadge status={game.status} />
        <span className="text-xs text-gray-400">
          Week {game.week} · {game.season}
        </span>
      </div>

      <div className="flex items-center justify-between">
        {/* Away team */}
        <div className="flex flex-col items-center gap-1">
          <span className="text-lg font-bold text-gray-900">{away.abbr}</span>
          {game.final_away_score != null && (
            <span className="text-2xl font-semibold tabular-nums text-gray-900">
              {game.final_away_score}
            </span>
          )}
        </div>

        <span className="text-sm font-medium text-gray-400">@</span>

        {/* Home team */}
        <div className="flex flex-col items-center gap-1">
          <span className="text-lg font-bold text-gray-900">{home.abbr}</span>
          {game.final_home_score != null && (
            <span className="text-2xl font-semibold tabular-nums text-gray-900">
              {game.final_home_score}
            </span>
          )}
        </div>
      </div>

      {game.home_wp != null && game.status !== 'final' && (
        <WpBar
          homeWp={game.home_wp}
          homeColor={home.primary_color ?? '#C60C30'}
          awayColor={away.primary_color ?? '#A5ACAF'}
        />
      )}

      {game.venue && (
        <p className="mt-2 truncate text-xs text-gray-400">{game.venue}</p>
      )}
    </Link>
  )
}
