import type { MomentumSwing } from '../../types/analytics'

interface MomentumPanelProps {
  swings: MomentumSwing[]
  isLoading?: boolean
  onSelect?: (sequence: number) => void
  selectedSequence?: number | null
}

function formatClock(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}

const TAG_LABELS: Record<string, string> = {
  turnover:    '🔄 Turnover',
  touchdown:   '🏈 Touchdown',
  field_goal:  '🎯 Field Goal',
  fourth_down: '4️⃣ 4th Down',
}

const RANK_COLORS: Record<number, { bg: string; text: string; border: string }> = {
  1: { bg: 'bg-red-50',    text: 'text-red-600',    border: 'border-red-300' },
  2: { bg: 'bg-orange-50', text: 'text-orange-500', border: 'border-orange-200' },
  3: { bg: 'bg-yellow-50', text: 'text-yellow-600', border: 'border-yellow-200' },
}

export function MomentumPanel({ swings, isLoading, onSelect, selectedSequence }: MomentumPanelProps) {
  return (
    <div className="rounded-xl border border-gray-200 bg-white shadow-sm">
      <div className="border-b border-gray-200 px-4 py-3">
        <h2 className="text-sm font-semibold text-gray-900">⚡ Momentum Swings</h2>
        <p className="mt-0.5 text-xs text-gray-400">Biggest win-probability shifts in the game</p>
      </div>

      <div className="divide-y divide-gray-100">
        {isLoading ? (
          <p className="px-4 py-6 text-center text-xs text-gray-400">Computing…</p>
        ) : swings.length === 0 ? (
          <p className="px-4 py-6 text-center text-xs text-gray-400">No data yet</p>
        ) : (
          swings.map((sw) => {
            const colors = RANK_COLORS[sw.rank] ?? RANK_COLORS[3]
            const isSelected = selectedSequence === sw.play_ref.sequence
            const deltaSign = sw.delta_wp > 0 ? '+' : ''
            const deltaPct = `${deltaSign}${Math.round(sw.delta_wp * 100)}%`
            return (
              <button
                key={sw.play_ref.play_id}
                onClick={() => onSelect?.(sw.play_ref.sequence)}
                className={`w-full cursor-pointer px-4 py-3 text-left transition-colors hover:bg-gray-50 ${isSelected ? 'bg-blue-50' : ''}`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span
                      className={`inline-flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full border text-xs font-bold ${colors.bg} ${colors.text} ${colors.border}`}
                    >
                      {sw.is_turning_point ? '⚡' : sw.rank}
                    </span>
                    <div>
                      <div className="flex items-center gap-1.5">
                        <span className="text-xs font-medium text-gray-500">
                          Q{sw.play_ref.quarter} · {formatClock(sw.play_ref.game_clock_seconds)}
                        </span>
                        {sw.tag && (
                          <span className={`rounded-full px-1.5 py-0.5 text-[10px] font-medium ${colors.bg} ${colors.text}`}>
                            {TAG_LABELS[sw.tag] ?? sw.tag}
                          </span>
                        )}
                        {sw.is_turning_point && (
                          <span className="rounded-full bg-red-100 px-1.5 py-0.5 text-[10px] font-semibold text-red-600">
                            Turning Point
                          </span>
                        )}
                      </div>
                      <p className="mt-0.5 line-clamp-2 text-xs text-gray-600">
                        {sw.play_ref.description ?? '—'}
                      </p>
                    </div>
                  </div>
                  <div className="flex-shrink-0 text-right">
                    <span className={`text-sm font-bold ${sw.delta_wp > 0 ? 'text-blue-600' : 'text-red-500'}`}>
                      {deltaPct}
                    </span>
                    <p className="text-[10px] text-gray-400">
                      {Math.round(sw.wp_before * 100)}% → {Math.round(sw.wp_after * 100)}%
                    </p>
                  </div>
                </div>
              </button>
            )
          })
        )}
      </div>
    </div>
  )
}
