import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ScoreHeader } from '../components/game-detail/ScoreHeader'
import { WpChart } from '../components/game-detail/WpChart'
import { ShapPanel } from '../components/game-detail/ShapPanel'
import { PlayLog } from '../components/game-detail/PlayLog'
import { MomentumPanel } from '../components/game-detail/MomentumPanel'
import { ClutchPanel } from '../components/game-detail/ClutchPanel'
import { DecisionGradesPanel } from '../components/game-detail/DecisionGradesPanel'
import { GameStatePanel } from '../components/game-detail/GameStatePanel'
import { ErrorBanner } from '../components/common/ErrorBanner'
import { Spinner } from '../components/common/Spinner'
import { useGame } from '../hooks/useGame'
import { useGameStream } from '../hooks/useGameStream'
import { useMomentumSwings, useClutchIndex, useDecisionGrades } from '../hooks/useAnalytics'
import type { WpDataPoint } from '../types/prediction'

export function GameDetailPage() {
  const { id } = useParams<{ id: string }>()
  const { data: game, isLoading, isError, error } = useGame(id)
  const streamState = useGameStream(id, game)
  const [selectedPlay, setSelectedPlay] = useState<WpDataPoint | null>(null)

  // Analytics — only enabled once we have plays
  const hasPlays = streamState.replayComplete || streamState.wpHistory.length > 0
  const { data: swingsData, isLoading: swingsLoading } = useMomentumSwings(id, hasPlays)
  const { data: clutchData, isLoading: clutchLoading } = useClutchIndex(id, hasPlays)
  const { data: decisionsData, isLoading: decisionsLoading } = useDecisionGrades(id, hasPlays)

  if (isLoading) {
    return (
      <div className="flex justify-center py-20">
        <Spinner />
      </div>
    )
  }

  if (isError || !game) {
    return (
      <div className="py-8">
        <ErrorBanner message={(error as Error)?.message ?? 'Game not found.'} />
        <Link to="/" className="mt-4 inline-block text-sm text-blue-600 underline">
          ← Back to games
        </Link>
      </div>
    )
  }

  const latestPlay = streamState.wpHistory[streamState.wpHistory.length - 1]
  const displayPlay = selectedPlay ?? latestPlay
  const swings = swingsData?.swings ?? []

  const handlePlaySelect = (play: WpDataPoint) => setSelectedPlay(play)
  const handleSeqSelect = (seq: number) => {
    const play = streamState.wpHistory.find((p) => p.sequence === seq)
    setSelectedPlay(play ?? null)
  }

  return (
    <div>
      <div className="mb-4">
        <Link to="/" className="text-sm text-blue-600 hover:underline">
          ← All games
        </Link>
      </div>

      {streamState.connectionState === 'error' && (
        <div className="mb-4 rounded-lg border border-red-300 bg-red-50 px-4 py-2 text-sm text-red-600">
          Live updates disconnected. Attempting to reconnect…
        </div>
      )}
      {streamState.replayComplete && (
        <div className="mb-4 rounded-lg border border-green-300 bg-green-50 px-4 py-2 text-sm text-green-700">
          Replay complete — {streamState.wpHistory.length} plays processed.
        </div>
      )}

      <div className="mb-4">
        <ScoreHeader
          game={game}
          currentHomeScore={latestPlay?.scoreHome}
          currentAwayScore={latestPlay?.scoreAway}
          currentQuarter={latestPlay?.quarter}
          currentClock={latestPlay?.gameClock}
        />
      </div>

      {/* WP Chart — passes swing markers and highlighted sequence */}
      <div className="mb-4">
        <WpChart
          data={streamState.wpHistory}
          homeTeam={game.home_team}
          awayTeam={game.away_team}
          onPlaySelect={handlePlaySelect}
          swings={swings}
          highlightedSequence={selectedPlay?.sequence ?? null}
        />
      </div>

      {/* Game State Panel — updates on every play selection */}
      <div className="mb-4">
        <GameStatePanel play={selectedPlay ?? latestPlay ?? null} game={game} />
      </div>

      {/* Row 1: SHAP + Play-by-Play */}
      <div className="mb-4 grid grid-cols-1 gap-4 lg:grid-cols-2">
        <ShapPanel
          features={displayPlay?.topShap ?? []}
          homeTeam={game.home_team}
          awayTeam={game.away_team}
          homeWp={displayPlay?.homeWp}
        />
        <PlayLog
          plays={streamState.wpHistory}
          selectedSequence={selectedPlay?.sequence ?? null}
          onSelect={handleSeqSelect}
        />
      </div>

      {/* Row 2: Momentum Swings + Clutch Moments */}
      <div className="mb-4 grid grid-cols-1 gap-4 lg:grid-cols-2">
        <MomentumPanel
          swings={swings}
          isLoading={swingsLoading}
          onSelect={handleSeqSelect}
          selectedSequence={selectedPlay?.sequence ?? null}
        />
        <ClutchPanel
          data={clutchData}
          isLoading={clutchLoading}
          homeTeam={game.home_team}
          awayTeam={game.away_team}
          onSelect={handleSeqSelect}
          selectedSequence={selectedPlay?.sequence ?? null}
        />
      </div>

      {/* Row 3: Coach Decisions — full width */}
      <div className="mb-4">
        <DecisionGradesPanel
          decisions={decisionsData?.decisions ?? []}
          isLoading={decisionsLoading}
          onSelect={handleSeqSelect}
          selectedSequence={selectedPlay?.sequence ?? null}
        />
      </div>
    </div>
  )
}
