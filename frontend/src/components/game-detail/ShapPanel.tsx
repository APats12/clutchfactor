import { Bar, BarChart, Cell, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { ShapFeature } from '../../types/prediction'
import type { Team } from '../../types/game'
import { Spinner } from '../common/Spinner'

interface ShapPanelProps {
  features: ShapFeature[]
  homeTeam: Team
  awayTeam: Team
  isLoading?: boolean
  homeWp?: number
}

export function ShapPanel({ features, homeTeam, awayTeam, isLoading, homeWp }: ShapPanelProps) {
  const homeColor = homeTeam.primary_color ?? '#C60C30'
  const awayColor = awayTeam.primary_color ?? '#A5ACAF'

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
      <div className="mb-1 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-gray-900">Why it changed</h2>
        {homeWp != null && (
          <span className="text-xs font-medium text-gray-500">
            {homeTeam.abbr}{' '}
            <span className="font-bold" style={{ color: homeColor }}>
              {Math.round(homeWp * 100)}%
            </span>{' '}
            win probability
          </span>
        )}
      </div>
      <p className="mb-3 text-xs text-gray-400">
        Factors pushing toward a {homeTeam.abbr} win (positive) or {awayTeam.abbr} win (negative)
      </p>

      {isLoading ? (
        <div className="flex h-40 items-center justify-center">
          <Spinner size="sm" />
        </div>
      ) : features.length === 0 ? (
        <p className="py-8 text-center text-xs text-gray-400">
          Click a point on the chart to see what drove the win probability.
        </p>
      ) : (
        <ResponsiveContainer width="100%" height={features.length * 40 + 20}>
          <BarChart
            data={features}
            layout="vertical"
            margin={{ top: 0, right: 16, left: 8, bottom: 0 }}
          >
            <XAxis
              type="number"
              domain={['auto', 'auto']}
              tick={{ fontSize: 10, fill: '#9ca3af' }}
              axisLine={{ stroke: '#e5e7eb' }}
              tickLine={false}
            />
            <YAxis
              type="category"
              dataKey="display_name"
              width={130}
              tick={{ fontSize: 11, fill: '#6b7280' }}
              axisLine={false}
              tickLine={false}
            />
            <ReferenceLine x={0} stroke="#e5e7eb" />
            <Tooltip
              contentStyle={{
                backgroundColor: '#ffffff',
                borderColor: '#e5e7eb',
                color: '#111827',
                fontSize: 12,
              }}
              formatter={(val: number) => [val.toFixed(3), 'SHAP value']}
              labelFormatter={(label: string) => label}
            />
            <Bar dataKey="shap_value" radius={[0, 3, 3, 0]}>
              {features.map((f, i) => (
                <Cell
                  key={i}
                  fill={f.direction === 'positive' ? homeColor : awayColor}
                  opacity={0.85}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}
