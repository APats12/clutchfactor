import type { GameStatus } from '../../types/game'

const STATUS_STYLES: Record<GameStatus, string> = {
  in_progress: 'border-green-500 text-green-700',
  scheduled:   'border-gray-400 text-gray-500',
  final:       'border-blue-500 text-blue-600',
}

const STATUS_LABELS: Record<GameStatus, string> = {
  in_progress: 'LIVE',
  scheduled:   'UPCOMING',
  final:       'FINAL',
}

export function StatusBadge({ status }: { status: GameStatus }) {
  return (
    <span
      className={`inline-flex items-center rounded border px-2 py-0.5 text-xs font-semibold tracking-wide bg-transparent ${STATUS_STYLES[status]}`}
    >
      {status === 'in_progress' && (
        <span className="mr-1.5 h-1.5 w-1.5 animate-pulse rounded-full bg-green-400" />
      )}
      {STATUS_LABELS[status]}
    </span>
  )
}
