interface DateSelectorProps {
  value: string
  onChange: (date: string) => void
}

export function DateSelector({ value, onChange }: DateSelectorProps) {
  return (
    <input
      type="date"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
    />
  )
}
