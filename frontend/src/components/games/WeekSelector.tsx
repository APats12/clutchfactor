type WeekValue = number | 'playoffs' | ''

interface WeekSelectorProps {
  value: WeekValue
  onChange: (week: WeekValue) => void
}

const REGULAR_SEASON_WEEKS = Array.from({ length: 18 }, (_, i) => i + 1)

export function WeekSelector({ value, onChange }: WeekSelectorProps) {
  return (
    <div className="flex flex-wrap gap-1.5">
      <button
        onClick={() => onChange('')}
        className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
          value === ''
            ? 'bg-blue-600 text-white'
            : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
        }`}
      >
        All weeks
      </button>
      {REGULAR_SEASON_WEEKS.map((w) => (
        <button
          key={w}
          onClick={() => onChange(w)}
          className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
            value === w
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
        >
          Wk {w}
        </button>
      ))}
      <button
        onClick={() => onChange('playoffs')}
        className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
          value === 'playoffs'
            ? 'bg-amber-500 text-white'
            : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
        }`}
      >
        Playoffs
      </button>
    </div>
  )
}
