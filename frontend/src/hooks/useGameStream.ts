import { useEffect, useReducer, useRef } from 'react'
import { gameStreamReducer, initialState } from '../store/gameStreamSlice'
import type { GameStreamState } from '../store/gameStreamSlice'
import type { SSEEvent } from '../types/sse'
import { fetchWpHistory } from '../api/games'
import { startReplay } from '../api/replay'
import type { GameDetail } from '../types/game'

export function useGameStream(
  gameId: string | undefined,
  game?: GameDetail,
): GameStreamState {
  const [state, dispatch] = useReducer(gameStreamReducer, initialState)
  const replayStarted = useRef(false)

  // On mount: fetch history from REST. If empty AND the game has a
  // nflfastr_game_id, auto-start the replay so the chart fills itself.
  useEffect(() => {
    if (!gameId) return
    replayStarted.current = false  // reset on gameId change

    fetchWpHistory(gameId)
      .then((history) => {
        if (history.length > 0) {
          dispatch({ type: 'SEED_HISTORY', payload: history })
        } else if (game?.nflfastr_game_id && !replayStarted.current) {
          // No history yet — kick off the replay automatically
          replayStarted.current = true
          const csv = `play_by_play_${game.season}.csv`
          startReplay(gameId, csv, game.nflfastr_game_id, 10).catch((err: Error) => {
            // 409 = already running, SSE will pick it up — ignore
            if (!String(err.message).includes('409')) {
              console.error('Failed to start replay:', err.message)
            }
          })
        }
      })
      .catch(() => {
        // Silently ignore — live SSE will populate the chart instead
      })
  }, [gameId, game?.nflfastr_game_id])

  useEffect(() => {
    if (!gameId) return
    if (state.replayComplete) return

    const source = new EventSource(`/api/v1/stream/games/${gameId}`)

    source.onopen = () => {
      dispatch({ type: 'SSE_OPEN' })
    }

    source.onmessage = (e: MessageEvent) => {
      try {
        const event: SSEEvent = JSON.parse(e.data as string)
        dispatch({ type: 'SSE_EVENT', payload: event })
        if (event.event_type === 'replay_complete') {
          source.close()
        }
      } catch {
        // Ignore heartbeat comments or malformed events
      }
    }

    source.onerror = () => {
      dispatch({ type: 'SSE_ERROR' })
    }

    return () => {
      source.close()
      dispatch({ type: 'SSE_CLOSED' })
    }
  }, [gameId, state.replayComplete])

  return state
}
