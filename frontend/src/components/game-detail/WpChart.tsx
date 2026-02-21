import {
  Area,
  AreaChart,
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { WpDataPoint } from '../../types/prediction'
import type { Team } from '../../types/game'
import type { MomentumSwing } from '../../types/analytics'

interface WpChartProps {
  data: WpDataPoint[]
  homeTeam: Team
  awayTeam: Team
  onPlaySelect?: (point: WpDataPoint) => void
  swings?: MomentumSwing[]
  highlightedSequence?: number | null
}

function formatClock(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}

/**
 * Convert quarter + gameClock (seconds remaining in game) to elapsed seconds
 * so the x-axis flows left → right: 0 = kickoff, 3600 = end of regulation.
 * Overtime quarters (5+) are appended after 3600.
 */
function toElapsed(quarter: number, gameClock: number): number {
  const regQuarter = Math.min(quarter, 4)
  const quarterStart = (regQuarter - 1) * 900
  const elapsedInQuarter = 900 - Math.min(gameClock, 900)
  if (quarter <= 4) return quarterStart + elapsedInQuarter
  // OT: each OT period is 10 min (600s)
  return 3600 + (quarter - 5) * 600 + (600 - Math.min(gameClock, 600))
}

// Quarter boundary lines in elapsed-seconds space
const QUARTER_LINES = [
  { x: 900,  label: 'Q2' },
  { x: 1800, label: 'Q3' },
  { x: 2700, label: 'Q4' },
]

// X-axis tick positions — one per quarter midpoint + start
const QUARTER_TICKS = [450, 1350, 2250, 3150]
const QUARTER_TICK_LABELS: Record<number, string> = {
  450:  'Q1',
  1350: 'Q2',
  2250: 'Q3',
  3150: 'Q4',
}

interface TooltipPayload {
  payload: WpDataPoint & { elapsed: number }
}

function CustomTooltip({ active, payload }: { active?: boolean; payload?: TooltipPayload[] }) {
  if (!active || !payload?.length) return null
  const d = payload[0].payload
  return (
    <div className="max-w-xs rounded-lg border border-gray-200 bg-white p-3 shadow-lg">
      <p className="text-xs font-semibold text-gray-500">
        Q{d.quarter} · {formatClock(d.gameClock)} · {d.scoreAway}–{d.scoreHome}
      </p>
      <p className="mt-1 line-clamp-2 text-xs text-gray-700">{d.description ?? '—'}</p>
      <div className="mt-2 flex justify-between text-xs font-medium">
        <span className="text-gray-500">Away: {Math.round(d.awayWp * 100)}%</span>
        <span className="text-blue-600">Home: {Math.round(d.homeWp * 100)}%</span>
      </div>
    </div>
  )
}

const TAG_COLORS: Record<string, string> = {
  turnover:    '#ef4444',
  touchdown:   '#22c55e',
  field_goal:  '#f59e0b',
  fourth_down: '#8b5cf6',
}

const SWING_LABEL_COLORS: Record<number, string> = {
  1: '#ef4444',
  2: '#f97316',
  3: '#eab308',
}

export function WpChart({
  data,
  homeTeam,
  awayTeam,
  onPlaySelect,
  swings = [],
  highlightedSequence,
}: WpChartProps) {
  const homeColor = homeTeam.primary_color ?? '#3b82f6'
  const awayColor = awayTeam.primary_color ?? '#9ca3af'

  if (data.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center rounded-xl border border-dashed border-gray-200 text-sm text-gray-400">
        Win probability will appear as plays come in…
      </div>
    )
  }

  // Attach elapsed seconds to each data point for the x-axis
  const chartData = data.map((d) => ({
    ...d,
    elapsed: toElapsed(d.quarter, d.gameClock),
  }))

  // Build a sequence → elapsed lookup for swing / highlight markers
  const seqToElapsed: Record<number, number> = {}
  for (const d of chartData) seqToElapsed[d.sequence] = d.elapsed

  const maxElapsed = chartData[chartData.length - 1]?.elapsed ?? 0
  const quarterLines = [
    ...QUARTER_LINES,
    ...(maxElapsed > 3600 ? [{ x: 3600, label: 'OT' }] : []),
  ]

  const xTicks = maxElapsed > 3600
    ? [...QUARTER_TICKS, 3900]
    : QUARTER_TICKS.filter((t) => t < maxElapsed + 450)

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-gray-900">Win Probability</h2>
        <div className="flex gap-4 text-xs">
          <span className="flex items-center gap-1.5 text-gray-500">
            <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: homeColor }} />
            {homeTeam.abbr} (home)
          </span>
          <span className="flex items-center gap-1.5 text-gray-500">
            <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: awayColor }} />
            {awayTeam.abbr} (away)
          </span>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={280}>
        <AreaChart
          data={chartData}
          margin={{ top: 4, right: 4, left: -20, bottom: 0 }}
          onClick={(e) => {
            if (e?.activePayload?.length && onPlaySelect) {
              onPlaySelect(e.activePayload[0].payload as WpDataPoint)
            }
          }}
        >
          <defs>
            <linearGradient id="homeGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={homeColor} stopOpacity={0.3} />
              <stop offset="95%" stopColor={homeColor} stopOpacity={0.0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" vertical={false} />
          <XAxis
            dataKey="elapsed"
            type="number"
            scale="linear"
            domain={[0, maxElapsed > 3600 ? maxElapsed + 60 : 3600]}
            ticks={xTicks}
            tickFormatter={(v: number) =>
              QUARTER_TICK_LABELS[v] ?? (v >= 3600 ? 'OT' : '')
            }
            tick={{ fontSize: 11, fontWeight: 600, fill: '#6b7280' }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            domain={[0, 1]}
            tickFormatter={(v: number) => `${Math.round(v * 100)}%`}
            tick={{ fontSize: 10, fill: '#9ca3af' }}
            axisLine={false}
            tickLine={false}
          />
          {/* Quarter boundary dividers */}
          {quarterLines.map(({ x, label }) => (
            <ReferenceLine
              key={x}
              x={x}
              stroke="#d1d5db"
              strokeDasharray="4 4"
              label={{ value: label, position: 'insideTopRight', fontSize: 10, fill: '#9ca3af' }}
            />
          ))}
          <ReferenceLine y={0.5} stroke="#e5e7eb" strokeDasharray="4 4" />

          {/* Momentum swing vertical markers */}
          {swings.map((sw) => {
            const xPos = seqToElapsed[sw.play_ref.sequence]
            if (xPos == null) return null
            const color = TAG_COLORS[sw.tag ?? ''] ?? (SWING_LABEL_COLORS[sw.rank] ?? '#9ca3af')
            return (
              <ReferenceLine
                key={`swing-${sw.play_ref.play_id}`}
                x={xPos}
                stroke={color}
                strokeWidth={sw.is_turning_point ? 2.5 : 1.5}
                strokeDasharray={sw.is_turning_point ? undefined : '3 3'}
                label={
                  sw.is_turning_point
                    ? { value: '⚡', position: 'insideTopLeft', fontSize: 13, fill: color }
                    : undefined
                }
              />
            )
          })}

          {/* Highlighted play (from panel clicks) */}
          {highlightedSequence != null && seqToElapsed[highlightedSequence] != null && (
            <ReferenceLine
              x={seqToElapsed[highlightedSequence]}
              stroke="#3b82f6"
              strokeWidth={2}
            />
          )}

          <Tooltip content={<CustomTooltip />} />
          <Area
            type="monotone"
            dataKey="homeWp"
            stroke={homeColor}
            strokeWidth={2}
            fill="url(#homeGrad)"
            dot={false}
            activeDot={{ r: 5 }}
            isAnimationActive={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
