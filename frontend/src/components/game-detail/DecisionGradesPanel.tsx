import type { CoachDecision, DecisionType, GradeLabel } from '../../types/analytics'

interface DecisionGradesPanelProps {
  decisions: CoachDecision[]
  isLoading?: boolean
  onSelect?: (sequence: number) => void
  selectedSequence?: number | null
}

function formatClock(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}

const GRADE_STYLES: Record<GradeLabel, { bg: string; text: string; border: string }> = {
  'Optimal':     { bg: 'bg-green-50',  text: 'text-green-700',  border: 'border-green-200' },
  'Questionable':{ bg: 'bg-yellow-50', text: 'text-yellow-700', border: 'border-yellow-200' },
  'Bad':         { bg: 'bg-red-50',    text: 'text-red-600',    border: 'border-red-200' },
  'Very Bad':    { bg: 'bg-red-100',   text: 'text-red-700',    border: 'border-red-300' },
}

const ACTION_LABELS: Record<DecisionType, string> = {
  go_for_it:   '🏈 Go for it',
  punt:        '👟 Punt',
  field_goal:  '🎯 Field Goal',
}

export function DecisionGradesPanel({
  decisions,
  isLoading,
  onSelect,
  selectedSequence,
}: DecisionGradesPanelProps) {
  return (
    <div className="rounded-xl border border-gray-200 bg-white shadow-sm">
      <div className="border-b border-gray-200 px-4 py-3">
        <h2 className="text-sm font-semibold text-gray-900">🎓 Coach Decisions</h2>
        <p className="mt-0.5 text-xs text-gray-400">4th-down graded by counterfactual win probability</p>
      </div>

      <div className="divide-y divide-gray-100">
        {isLoading ? (
          <p className="px-4 py-6 text-center text-xs text-gray-400">Computing…</p>
        ) : decisions.length === 0 ? (
          <p className="px-4 py-6 text-center text-xs text-gray-400">No 4th-down decisions yet</p>
        ) : (
          decisions.map((d) => {
            const gradeStyle = GRADE_STYLES[d.grade]
            const isSelected = selectedSequence === d.play_ref.sequence
            const didChooseBest = d.actual_type === d.best_action
            return (
              <button
                key={d.play_ref.play_id}
                onClick={() => onSelect?.(d.play_ref.sequence)}
                className={`w-full cursor-pointer px-4 py-3 text-left transition-colors hover:bg-gray-50 ${isSelected ? 'bg-blue-50' : ''}`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0 flex-1">
                    {/* Situation line */}
                    <div className="flex flex-wrap items-center gap-1.5">
                      <span className="text-xs font-semibold text-gray-700">{d.situation}</span>
                      <span className="text-[10px] text-gray-400">
                        Q{d.play_ref.quarter} · {formatClock(d.play_ref.game_clock_seconds)}
                      </span>
                    </div>

                    {/* Chosen vs. best action row */}
                    <div className="mt-1.5 flex flex-wrap gap-2 text-[11px]">
                      <span className="flex items-center gap-1 rounded-full bg-gray-100 px-2 py-0.5 text-gray-600">
                        Chose: {ACTION_LABELS[d.actual_type]}
                      </span>
                      {!didChooseBest && (
                        <span className="flex items-center gap-1 rounded-full bg-blue-50 px-2 py-0.5 text-blue-600">
                          Best: {ACTION_LABELS[d.best_action as DecisionType] ?? d.best_action}
                        </span>
                      )}
                    </div>

                    {/* Alternatives summary */}
                    <div className="mt-1.5 flex flex-wrap gap-1.5">
                      {Object.entries(d.alternatives).map(([action, opt]) => {
                        if (!opt) return null
                        const isChosen = action === d.actual_type
                        const isBest = action === d.best_action
                        return (
                          <span
                            key={action}
                            className={`rounded px-1.5 py-0.5 text-[10px] font-medium ${
                              isChosen && isBest
                                ? 'bg-green-100 text-green-700'
                                : isChosen
                                ? 'bg-gray-100 text-gray-600'
                                : isBest
                                ? 'bg-blue-100 text-blue-700'
                                : 'bg-gray-50 text-gray-400'
                            }`}
                          >
                            {action.replace('_', ' ')} {Math.round(opt.wp * 100)}%
                            {opt.detail ? ` (${opt.detail})` : ''}
                          </span>
                        )
                      })}
                    </div>
                  </div>

                  {/* Grade badge */}
                  <div className="flex-shrink-0 text-right">
                    <span
                      className={`inline-block rounded-full border px-2 py-0.5 text-xs font-bold ${gradeStyle.bg} ${gradeStyle.text} ${gradeStyle.border}`}
                    >
                      {d.grade_emoji} {d.grade}
                    </span>
                    <p className="mt-1 text-[10px] text-gray-400">
                      Δ {d.decision_delta > 0 ? '+' : ''}{Math.round(d.decision_delta * 100)}%
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
