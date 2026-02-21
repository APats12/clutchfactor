import type { WpDataPoint } from '../../types/prediction'

interface PlayLogProps {
  plays: WpDataPoint[]
  selectedSequence: number | null
  onSelect: (sequence: number) => void
}

function formatClock(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}

export function PlayLog({ plays, selectedSequence, onSelect }: PlayLogProps) {
  return (
    <div className="rounded-xl border border-gray-200 bg-white shadow-sm">
      <div className="border-b border-gray-200 px-4 py-3">
        <h2 className="text-sm font-semibold text-gray-900">Play-by-Play</h2>
      </div>
      <div className="h-80 overflow-y-auto">
        {plays.length === 0 ? (
          <p className="py-8 text-center text-xs text-gray-400">No plays yet…</p>
        ) : (
          <ul>
            {[...plays].reverse().map((p) => (
              <li
                key={p.sequence}
                onClick={() => onSelect(p.sequence)}
                className={`cursor-pointer border-b border-gray-100 px-4 py-2.5 transition-colors hover:bg-gray-50 ${
                  selectedSequence === p.sequence ? 'bg-blue-50' : ''
                }`}
              >
                <div className="flex items-baseline justify-between">
                  <span className="text-xs font-medium text-gray-500">
                    Q{p.quarter} · {formatClock(p.gameClock)}
                  </span>
                  <span className="text-xs text-gray-400">
                    {p.scoreAway}–{p.scoreHome}
                  </span>
                </div>
                <p className="mt-0.5 line-clamp-2 text-xs text-gray-700">
                  {p.description ?? '—'}
                </p>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
