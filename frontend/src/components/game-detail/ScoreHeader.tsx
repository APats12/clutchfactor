import type { GameDetail } from '../../types/game'
import { StatusBadge } from '../common/Badge'

interface ScoreHeaderProps {
  game: GameDetail
  currentHomeScore?: number
  currentAwayScore?: number
  currentQuarter?: number
  currentClock?: number
}

function formatClock(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}

export function ScoreHeader({
  game,
  currentHomeScore,
  currentAwayScore,
  currentQuarter,
  currentClock,
}: ScoreHeaderProps) {
  const homeScore = currentHomeScore ?? game.final_home_score ?? 0
  const awayScore = currentAwayScore ?? game.final_away_score ?? 0

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
      <div className="mb-4 flex items-center justify-between">
        <StatusBadge status={game.status} />
        {currentQuarter != null && currentClock != null && (
          <span className="text-sm font-medium text-gray-600">
            Q{currentQuarter} · {formatClock(currentClock)}
          </span>
        )}
        <span className="text-sm text-gray-400">
          Week {game.week} · {game.season} · {game.venue ?? 'TBD'}
        </span>
      </div>

      <div className="flex items-center justify-around">
        {/* Away */}
        <div className="flex flex-col items-center">
          <div
            className="mb-2 flex h-14 w-14 items-center justify-center rounded-full text-xl font-black text-white"
            style={{ backgroundColor: game.away_team.primary_color ?? '#6b7280' }}
          >
            {game.away_team.abbr}
          </div>
          <span className="text-sm text-gray-500">{game.away_team.name}</span>
          <span className="mt-1 text-4xl font-bold tabular-nums text-gray-900">
            {awayScore}
          </span>
        </div>

        <span className="text-2xl font-light text-gray-300">vs</span>

        {/* Home */}
        <div className="flex flex-col items-center">
          <div
            className="mb-2 flex h-14 w-14 items-center justify-center rounded-full text-xl font-black text-white"
            style={{ backgroundColor: game.home_team.primary_color ?? '#3b82f6' }}
          >
            {game.home_team.abbr}
          </div>
          <span className="text-sm text-gray-500">{game.home_team.name}</span>
          <span className="mt-1 text-4xl font-bold tabular-nums text-gray-900">
            {homeScore}
          </span>
        </div>
      </div>
    </div>
  )
}
