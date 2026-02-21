interface SeasonSelectorProps {
  value: number | ''
  onChange: (season: number | '') => void
  seasons: number[]
}

export function SeasonSelector({ value, onChange, seasons }: SeasonSelectorProps) {
  return (
    <div className="flex gap-2">
      <button
        onClick={() => onChange('')}
        className={`rounded-full px-4 py-1.5 text-sm font-medium transition-colors ${
          value === ''
            ? 'bg-blue-600 text-white'
            : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
        }`}
      >
        All
      </button>
      {seasons.map((s) => (
        <button
          key={s}
          onClick={() => onChange(s)}
          className={`rounded-full px-4 py-1.5 text-sm font-medium transition-colors ${
            value === s
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
        >
          {s}
        </button>
      ))}
    </div>
  )
}
