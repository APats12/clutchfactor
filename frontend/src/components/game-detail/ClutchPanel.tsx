import type { ClutchResponse } from '../../types/analytics'
import type { Team } from '../../types/game'

interface ClutchPanelProps {
  data: ClutchResponse | undefined
  isLoading?: boolean
  homeTeam: Team
  awayTeam: Team
  onSelect?: (sequence: number) => void
  selectedSequence?: number | null
}

function formatClock(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}

function ClutchBar({ value, max, color }: { value: number; max: number; color: string }) {
  const pct = max > 0 ? Math.round((value / max) * 100) : 0
  return (
    <div className="h-1.5 w-full overflow-hidden rounded-full bg-gray-100">
      <div
        className="h-full rounded-full transition-all"
        style={{ width: `${pct}%`, backgroundColor: color }}
      />
    </div>
  )
}

export function ClutchPanel({
  data,
  isLoading,
  homeTeam,
  awayTeam,
  onSelect,
  selectedSequence,
}: ClutchPanelProps) {
  const homeColor = homeTeam.primary_color ?? '#3b82f6'
  const awayColor = awayTeam.primary_color ?? '#9ca3af'

  const topPlays = data?.top_plays ?? []
  const maxClutch = topPlays[0]?.clutch_score ?? 1

  const homeOff = data?.team_totals.home.offense ?? 0
  const homeDef = data?.team_totals.home.defense ?? 0
  const awayOff = data?.team_totals.away.offense ?? 0
  const awayDef = data?.team_totals.away.defense ?? 0
  const teamMax = Math.max(homeOff, homeDef, awayOff, awayDef, 0.01)

  return (
    <div className="rounded-xl border border-gray-200 bg-white shadow-sm">
      <div className="border-b border-gray-200 px-4 py-3">
        <h2 className="text-sm font-semibold text-gray-900">🔥 Clutch Moments</h2>
        <p className="mt-0.5 text-xs text-gray-400">High-leverage plays late in a close game</p>
      </div>

      {/* Top plays list */}
      <div className="divide-y divide-gray-100">
        {isLoading ? (
          <p className="px-4 py-6 text-center text-xs text-gray-400">Computing…</p>
        ) : topPlays.length === 0 ? (
          <p className="px-4 py-6 text-center text-xs text-gray-400">No data yet</p>
        ) : (
          topPlays.map((play) => {
            const isSelected = selectedSequence === play.play_ref.sequence
            return (
              <button
                key={play.play_ref.play_id}
                onClick={() => onSelect?.(play.play_ref.sequence)}
                className={`w-full cursor-pointer px-4 py-2.5 text-left transition-colors hover:bg-gray-50 ${isSelected ? 'bg-blue-50' : ''}`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <div className="flex items-center gap-1.5">
                      <span className="text-xs font-medium text-gray-500">
                        #{play.rank} · Q{play.play_ref.quarter} · {formatClock(play.play_ref.game_clock_seconds)}
                      </span>
                      <span className="text-[10px] text-gray-400">
                        diff {play.score_diff > 0 ? '+' : ''}{play.score_diff}
                      </span>
                    </div>
                    <p className="mt-0.5 line-clamp-1 text-xs text-gray-600">
                      {play.play_ref.description ?? '—'}
                    </p>
                    <div className="mt-1">
                      <ClutchBar value={play.clutch_score} max={maxClutch} color="#f97316" />
                    </div>
                  </div>
                  <div className="flex-shrink-0 text-right">
                    <span className="text-sm font-bold text-orange-500">
                      {play.clutch_score.toFixed(3)}
                    </span>
                    <p className="text-[10px] text-gray-400">
                      ΔWP {play.delta_wp > 0 ? '+' : ''}{Math.round(play.delta_wp * 100)}%
                    </p>
                  </div>
                </div>
              </button>
            )
          })
        )}
      </div>

      {/* Team totals bar chart */}
      {data && (homeOff + homeDef + awayOff + awayDef) > 0 && (
        <div className="border-t border-gray-100 px-4 py-3">
          <p className="mb-2 text-xs font-semibold text-gray-500">Clutch Totals by Team</p>
          <div className="space-y-2">
            {[
              { label: `${homeTeam.abbr} Off`, value: homeOff, color: homeColor },
              { label: `${homeTeam.abbr} Def`, value: homeDef, color: homeColor, opacity: 0.5 },
              { label: `${awayTeam.abbr} Off`, value: awayOff, color: awayColor },
              { label: `${awayTeam.abbr} Def`, value: awayDef, color: awayColor, opacity: 0.5 },
            ].map(({ label, value, color, opacity }) => (
              <div key={label} className="flex items-center gap-2">
                <span className="w-16 flex-shrink-0 text-right text-[10px] text-gray-500">{label}</span>
                <div className="flex-1">
                  <ClutchBar
                    value={value}
                    max={teamMax}
                    color={opacity ? color + '80' : color}
                  />
                </div>
                <span className="w-10 text-[10px] text-gray-400">{value.toFixed(2)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
