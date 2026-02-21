import type { WpDataPoint } from '../../types/prediction'
import type { Game } from '../../types/game'

interface GameStatePanelProps {
  play: WpDataPoint | null
  game: Game
}

function formatClock(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}

function ordinal(n: number): string {
  if (n === 1) return '1st'
  if (n === 2) return '2nd'
  if (n === 3) return '3rd'
  return `${n}th`
}

function getSpecialSituation(playType: string | null | undefined): string | null {
  if (!playType) return null
  const pt = playType.toLowerCase()
  if (pt === 'kickoff') return 'Kickoff'
  if (pt === 'extra_point' || pt === 'pat') return 'Extra Point Attempt'
  if (pt === 'two_point_attempt') return '2-Point Conversion'
  if (pt === 'end_of_quarter' || pt === 'end_of_half' || pt === 'end_of_game') return 'Game End'
  return null
}

interface FieldProps {
  losPosition: number        // 0–100, 0 = home EZ, 100 = away EZ
  firstDownPosition: number | null
  isGoalToGo: boolean
  movingRight: boolean
  possessionColor: string
  homeAbbr: string
  awayAbbr: string
}

function MiniField({
  losPosition,
  firstDownPosition,
  isGoalToGo,
  movingRight,
  possessionColor,
  homeAbbr,
  awayAbbr,
}: FieldProps) {
  const EZ = 8 // end-zone width in percent of total bar

  // Map 0–100 yard scale into the playable portion (EZ% … 100-EZ%)
  const toX = (yard: number) => EZ + (yard / 100) * (100 - 2 * EZ)

  const losX = Math.min(Math.max(toX(losPosition), EZ), 100 - EZ)
  const fdX =
    firstDownPosition != null && !isGoalToGo
      ? Math.min(Math.max(toX(firstDownPosition), EZ), 100 - EZ)
      : null

  return (
    <div className="relative w-full" style={{ height: 52 }}>
      {/* ── playing field ── */}
      <div
        className="absolute inset-0 rounded overflow-hidden"
        style={{ backgroundColor: '#2d6a4f' }}
      >
        {/* left end zone */}
        <div
          className="absolute top-0 bottom-0 flex items-center justify-center"
          style={{ left: 0, width: `${EZ}%`, backgroundColor: '#1b4332' }}
        >
          <span
            className="text-white font-bold select-none"
            style={{ fontSize: 9, letterSpacing: '0.05em', writingMode: 'vertical-rl', transform: 'rotate(180deg)' }}
          >
            {homeAbbr}
          </span>
        </div>

        {/* right end zone */}
        <div
          className="absolute top-0 bottom-0 flex items-center justify-center"
          style={{ right: 0, width: `${EZ}%`, backgroundColor: '#1b4332' }}
        >
          <span
            className="text-white font-bold select-none"
            style={{ fontSize: 9, letterSpacing: '0.05em', writingMode: 'vertical-rl' }}
          >
            {awayAbbr}
          </span>
        </div>

        {/* yard lines every 10 yards */}
        {[10, 20, 30, 40, 50, 60, 70, 80, 90].map((y) => (
          <div
            key={y}
            className="absolute top-0 bottom-0"
            style={{
              left: `${toX(y)}%`,
              width: 1,
              backgroundColor: y === 50 ? 'rgba(255,255,255,0.35)' : 'rgba(255,255,255,0.15)',
            }}
          />
        ))}

        {/* ── first-down marker (solid yellow) ── */}
        {fdX != null && (
          <div
            className="absolute top-0 bottom-0"
            style={{ left: `${fdX}%`, width: 2, backgroundColor: '#fbbf24' }}
          />
        )}

        {/* ── LOS marker — bright white ── */}
        <div
          className="absolute top-0 bottom-0"
          style={{ left: `${losX}%`, width: 2.5, backgroundColor: 'rgba(255,255,255,0.95)' }}
        />
      </div>

      {/* ── possession indicator: triangle cap + direction arrow ABOVE field ── */}
      {/* Triangle pointing down at LOS */}
      <div
        className="absolute"
        style={{
          left: `${losX}%`,
          top: -1,
          transform: 'translateX(-50%)',
          width: 0,
          height: 0,
          borderLeft: '6px solid transparent',
          borderRight: '6px solid transparent',
          borderTop: `8px solid ${possessionColor}`,
        }}
      />

      {/* Direction arrow to the side of the triangle */}
      <div
        className="absolute flex items-center"
        style={{
          top: -14,
          left: movingRight ? `calc(${losX}% + 10px)` : undefined,
          right: movingRight ? undefined : `calc(${100 - losX}% + 10px)`,
          color: possessionColor,
          fontSize: 10,
          fontWeight: 700,
          lineHeight: 1,
        }}
      >
        {movingRight ? '▶' : '◀'}
      </div>

      {/* ── yard labels: "50" at midfield, LOS yardline ── */}
      <div
        className="absolute bottom-1 text-white select-none pointer-events-none"
        style={{ left: `${toX(50)}%`, transform: 'translateX(-50%)', fontSize: 8, opacity: 0.5 }}
      >
        50
      </div>
    </div>
  )
}

export function GameStatePanel({ play, game }: GameStatePanelProps) {
  const homeAbbr = game.home_team.abbr
  const awayAbbr = game.away_team.abbr
  const homeColor = game.home_team.primary_color ?? '#3b82f6'
  const awayColor = game.away_team.primary_color ?? '#9ca3af'

  if (!play) {
    return (
      <div className="flex h-28 items-center justify-center rounded-xl border border-dashed border-gray-200 bg-white text-sm text-gray-400 shadow-sm">
        Select a play to see game state
      </div>
    )
  }

  const { quarter, gameClock, scoreHome, scoreAway, down, yardsToGo, yardLineFromOwn, playType, description, posteamAbbr } = play

  const special = getSpecialSituation(playType)

  // Possession
  const possessionAbbr = posteamAbbr ?? (() => {
    if (!description) return null
    const up = description.toUpperCase()
    if (up.startsWith(homeAbbr.toUpperCase())) return homeAbbr
    if (up.startsWith(awayAbbr.toUpperCase())) return awayAbbr
    return null
  })()
  const possessionIsHome = possessionAbbr === homeAbbr
  const possessionColor = possessionIsHome ? homeColor : awayColor

  // yard_line_from_own = 100 - yardline_100
  // yardline_100 = yards to opponent EZ (1=opp 1yd, 50=mid, 99=own 1yd)
  const ylFromOwn = yardLineFromOwn != null ? Math.abs(yardLineFromOwn) : null
  const yardline100 = ylFromOwn != null ? 100 - ylFromOwn : null

  // Yard line label
  const yardlineLabel = (() => {
    if (yardline100 == null) return null
    if (yardline100 === 50) return 'Midfield'
    if (yardline100 < 50) {
      return `${possessionIsHome ? awayAbbr : homeAbbr} ${yardline100}`
    }
    return `${possessionAbbr ?? 'OWN'} ${100 - yardline100}`
  })()

  // Field position (0=home EZ, 100=away EZ)
  let losPosition: number | null = null
  let firstDownPosition: number | null = null
  const movingRight = possessionIsHome

  if (yardline100 != null) {
    losPosition = possessionIsHome ? 100 - yardline100 : yardline100
    if (yardsToGo != null) {
      firstDownPosition = possessionIsHome
        ? Math.min(losPosition + yardsToGo, 100)
        : Math.max(losPosition - yardsToGo, 0)
    }
  }

  const isGoalToGo = yardline100 != null && yardsToGo != null && yardline100 === yardsToGo
  const isGameEnd = special === 'Game End'

  const situationLine = (() => {
    if (isGameEnd) return 'Final'
    if (special) return special
    if (down != null && yardsToGo != null) {
      return isGoalToGo ? `${ordinal(down)} & Goal` : `${ordinal(down)} & ${yardsToGo}`
    }
    return '—'
  })()

  const showField = losPosition != null && !isGameEnd

  return (
    <div className="rounded-xl border border-gray-200 bg-white shadow-sm overflow-hidden">
      <div className="px-4 pt-3 pb-3">
        {/* ── single info row ── */}
        <div className="flex items-center justify-between gap-4">
          {/* Left block: down/distance + field position */}
          <div className="flex items-baseline gap-3 min-w-0">
            <span
              className="text-xl font-bold leading-none tracking-tight whitespace-nowrap"
              style={{ color: isGameEnd ? '#374151' : possessionColor }}
            >
              {situationLine}
            </span>
            {yardlineLabel && !isGameEnd && (
              <span className="text-sm text-gray-400 whitespace-nowrap">
                {yardlineLabel}
              </span>
            )}
            {possessionAbbr && !isGameEnd && (
              <span
                className="text-xs font-semibold px-1.5 py-0.5 rounded whitespace-nowrap"
                style={{ backgroundColor: `${possessionColor}18`, color: possessionColor }}
              >
                {possessionAbbr}
              </span>
            )}
          </div>

          {/* Right block: quarter · clock + score */}
          <div className="flex-shrink-0 flex items-center gap-4">
            <span className="text-xs font-semibold text-gray-500 whitespace-nowrap">
              {isGameEnd ? 'Final' : `Q${quarter} · ${formatClock(gameClock)}`}
            </span>
            {/* Score display */}
            <div className="flex items-center gap-1.5 text-sm font-semibold whitespace-nowrap">
              <span style={{ color: awayColor }}>{awayAbbr}</span>
              <span className="text-gray-800">{scoreAway}</span>
              <span className="text-gray-300">–</span>
              <span className="text-gray-800">{scoreHome}</span>
              <span style={{ color: homeColor }}>{homeAbbr}</span>
            </div>
          </div>
        </div>

        {/* ── mini field ── */}
        {showField && losPosition != null && (
          <div className="mt-3">
            <MiniField
              losPosition={losPosition}
              firstDownPosition={firstDownPosition}
              isGoalToGo={isGoalToGo}
              movingRight={movingRight}
              possessionColor={possessionColor}
              homeAbbr={homeAbbr}
              awayAbbr={awayAbbr}
            />
            {/* ── compact legend ── */}
            <div className="mt-1.5 flex items-center gap-3 text-xs text-gray-400">
              <span className="flex items-center gap-1">
                <span className="inline-block h-2.5 w-0.5 bg-white border border-gray-300 rounded-full" />
                LOS
              </span>
              {!isGoalToGo && firstDownPosition != null && (
                <span className="flex items-center gap-1">
                  <span className="inline-block h-2.5 w-0.5 rounded-full" style={{ backgroundColor: '#fbbf24' }} />
                  1st Down
                </span>
              )}
              {isGoalToGo && (
                <span className="font-medium text-amber-500">Goal to Go</span>
              )}
            </div>
          </div>
        )}

        {/* ── game-end banner ── */}
        {isGameEnd && (
          <div className="mt-2 rounded-lg bg-gray-50 px-3 py-1.5 text-center text-sm font-semibold text-gray-600">
            {scoreAway > scoreHome
              ? `${awayAbbr} wins · ${scoreAway}–${scoreHome}`
              : scoreHome > scoreAway
                ? `${homeAbbr} wins · ${scoreHome}–${scoreAway}`
                : `Overtime · ${awayAbbr} ${scoreAway}–${scoreHome} ${homeAbbr}`}
          </div>
        )}
      </div>
    </div>
  )
}
