import { useState } from 'react'
import { DateSelector } from '../components/games/DateSelector'
import { GamesList } from '../components/games/GamesList'
import { SeasonSelector } from '../components/games/SeasonSelector'
import { StatusFilter } from '../components/games/StatusFilter'
import { TeamFilter } from '../components/games/TeamFilter'
import { WeekSelector } from '../components/games/WeekSelector'
import { ErrorBanner } from '../components/common/ErrorBanner'
import { Spinner } from '../components/common/Spinner'
import { useGames } from '../hooks/useGames'

const AVAILABLE_SEASONS = [2025, 2023, 2022]

type WeekValue = number | 'playoffs' | ''

export function GamesPage() {
  const [date, setDate] = useState('')
  const [status, setStatus] = useState('')
  const [season, setSeason] = useState<number | ''>(2025)
  const [week, setWeek] = useState<WeekValue>('')
  const [teamFilter, setTeamFilter] = useState('')

  function handleSeasonChange(s: number | '') {
    setSeason(s)
    setWeek('')
  }

  const params = {
    ...(date ? { date } : {}),
    ...(status ? { status } : {}),
    ...(season !== '' ? { season } : {}),
    ...(week === 'playoffs' ? { playoffs: true } : week !== '' ? { week } : {}),
  }

  const { data: games, isLoading, isError, error, refetch } = useGames(params)

  // Client-side team filter — applied on top of server-side filters
  const visibleGames = games && teamFilter
    ? games.filter(
        (g) => g.home_team.abbr === teamFilter || g.away_team.abbr === teamFilter,
      )
    : games

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">NFL Games</h1>
        <p className="mt-1 text-sm text-gray-500">
          Live win probability powered by XGBoost + SHAP
        </p>
      </div>

      <div className="mb-3 flex flex-wrap items-center gap-3">
        <SeasonSelector value={season} onChange={handleSeasonChange} seasons={AVAILABLE_SEASONS} />
      </div>

      {season !== '' && (
        <div className="mb-4">
          <WeekSelector value={week} onChange={setWeek} />
        </div>
      )}

      <div className="mb-4 flex flex-wrap items-center gap-3">
        <StatusFilter value={status} onChange={setStatus} />
        <DateSelector value={date} onChange={setDate} />
        {/* Team filter — populated from the fetched game list */}
        {games && games.length > 0 && (
          <TeamFilter games={games} value={teamFilter} onChange={setTeamFilter} />
        )}
        {date && (
          <button
            onClick={() => setDate('')}
            className="text-xs text-gray-400 hover:text-gray-600 underline"
          >
            Clear date
          </button>
        )}
      </div>

      {isLoading && (
        <div className="flex justify-center py-16">
          <Spinner />
        </div>
      )}

      {isError && (
        <ErrorBanner
          message={(error as Error)?.message ?? 'Failed to load games.'}
          onRetry={() => refetch()}
        />
      )}

      {visibleGames && <GamesList games={visibleGames} />}
    </div>
  )
}
