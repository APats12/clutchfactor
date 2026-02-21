interface StatusFilterProps {
  value: string
  onChange: (status: string) => void
}

const OPTIONS: { label: string; value: string }[] = [
  { label: 'All', value: '' },
  { label: 'Live', value: 'in_progress' },
  { label: 'Final', value: 'final' },
  { label: 'Upcoming', value: 'scheduled' },
]

export function StatusFilter({ value, onChange }: StatusFilterProps) {
  return (
    <div className="flex gap-2">
      {OPTIONS.map((opt) => (
        <button
          key={opt.value}
          onClick={() => onChange(opt.value)}
          className={`rounded-full px-4 py-1.5 text-sm font-medium transition-colors ${
            value === opt.value
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
        >
          {opt.label}
        </button>
      ))}
    </div>
  )
}
