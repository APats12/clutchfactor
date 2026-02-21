import { useState, useRef, useEffect } from 'react'
import type { Game } from '../../types/game'

interface TeamFilterProps {
  games: Game[]
  value: string   // selected team abbr, or ''
  onChange: (abbr: string) => void
}

export function TeamFilter({ games, value, onChange }: TeamFilterProps) {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const ref = useRef<HTMLDivElement>(null)

  // Derive sorted unique teams from current game list
  const teamMap = new Map<string, { abbr: string; name: string; color: string | null }>()
  for (const g of games) {
    if (!teamMap.has(g.home_team.abbr)) {
      teamMap.set(g.home_team.abbr, {
        abbr: g.home_team.abbr,
        name: g.home_team.name,
        color: g.home_team.primary_color,
      })
    }
    if (!teamMap.has(g.away_team.abbr)) {
      teamMap.set(g.away_team.abbr, {
        abbr: g.away_team.abbr,
        name: g.away_team.name,
        color: g.away_team.primary_color,
      })
    }
  }
  const teams = [...teamMap.values()].sort((a, b) => a.abbr.localeCompare(b.abbr))

  const filtered = query.trim()
    ? teams.filter(
        (t) =>
          t.abbr.toLowerCase().includes(query.toLowerCase()) ||
          t.name.toLowerCase().includes(query.toLowerCase()),
      )
    : teams

  const selected = teams.find((t) => t.abbr === value)

  // Close on outside click
  useEffect(() => {
    function handle(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false)
        setQuery('')
      }
    }
    document.addEventListener('mousedown', handle)
    return () => document.removeEventListener('mousedown', handle)
  }, [])

  function pick(abbr: string) {
    onChange(abbr)
    setOpen(false)
    setQuery('')
  }

  function clear(e: React.MouseEvent) {
    e.stopPropagation()
    onChange('')
    setOpen(false)
    setQuery('')
  }

  return (
    <div ref={ref} className="relative">
      {/* Trigger button */}
      <button
        onClick={() => setOpen((o) => !o)}
        className={`flex items-center gap-2 rounded-full border px-3 py-1.5 text-sm font-medium transition-colors ${
          value
            ? 'border-blue-500 bg-blue-50 text-blue-700'
            : 'border-gray-200 bg-gray-100 text-gray-600 hover:bg-gray-200'
        }`}
      >
        {selected ? (
          <>
            <span
              className="h-2 w-2 rounded-full flex-shrink-0"
              style={{ backgroundColor: selected.color ?? '#6b7280' }}
            />
            {selected.abbr}
          </>
        ) : (
          <>
            <svg className="h-3.5 w-3.5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 4h18M7 8h10M10 12h4" />
            </svg>
            Team
          </>
        )}
        {value ? (
          <span
            onClick={clear}
            className="ml-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-blue-200 text-blue-700 hover:bg-blue-300 text-xs leading-none"
          >
            ×
          </span>
        ) : (
          <svg className="h-3 w-3 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
          </svg>
        )}
      </button>

      {/* Dropdown */}
      {open && (
        <div className="absolute left-0 top-full z-30 mt-1.5 w-56 overflow-hidden rounded-xl border border-gray-200 bg-white shadow-lg">
          {/* Search */}
          <div className="border-b border-gray-100 px-3 py-2">
            <input
              autoFocus
              type="text"
              placeholder="Search teams…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="w-full bg-transparent text-sm text-gray-700 placeholder-gray-400 outline-none"
            />
          </div>

          {/* Team list */}
          <ul className="max-h-60 overflow-y-auto py-1">
            {filtered.length === 0 ? (
              <li className="px-3 py-2 text-xs text-gray-400">No teams found</li>
            ) : (
              filtered.map((t) => (
                <li key={t.abbr}>
                  <button
                    onClick={() => pick(t.abbr)}
                    className={`flex w-full items-center gap-2.5 px-3 py-2 text-left text-sm transition-colors hover:bg-gray-50 ${
                      t.abbr === value ? 'bg-blue-50 text-blue-700 font-medium' : 'text-gray-700'
                    }`}
                  >
                    <span
                      className="h-2.5 w-2.5 flex-shrink-0 rounded-full"
                      style={{ backgroundColor: t.color ?? '#6b7280' }}
                    />
                    <span className="w-9 font-semibold tabular-nums">{t.abbr}</span>
                    <span className="truncate text-xs text-gray-400">{t.name}</span>
                    {t.abbr === value && (
                      <svg className="ml-auto h-3.5 w-3.5 text-blue-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                      </svg>
                    )}
                  </button>
                </li>
              ))
            )}
          </ul>
        </div>
      )}
    </div>
  )
}
