import type { WpDataPoint } from '../types/prediction'
import type { SSEEvent } from '../types/sse'

export type ConnectionState = 'connecting' | 'open' | 'error' | 'closed'

export interface GameStreamState {
  wpHistory: WpDataPoint[]
  connectionState: ConnectionState
  lastEventAt: number | null
  replayComplete: boolean
}

export const initialState: GameStreamState = {
  wpHistory: [],
  connectionState: 'connecting',
  lastEventAt: null,
  replayComplete: false,
}

export type StreamAction =
  | { type: 'SSE_OPEN' }
  | { type: 'SSE_ERROR' }
  | { type: 'SSE_CLOSED' }
  | { type: 'SSE_EVENT'; payload: SSEEvent }
  | { type: 'RESET' }
  | { type: 'SEED_HISTORY'; payload: WpDataPoint[] }

export function gameStreamReducer(
  state: GameStreamState,
  action: StreamAction,
): GameStreamState {
  switch (action.type) {
    case 'SSE_OPEN':
      return { ...state, connectionState: 'open' }

    case 'SSE_ERROR':
      return { ...state, connectionState: 'error' }

    case 'SSE_CLOSED':
      return { ...state, connectionState: 'closed' }

    case 'RESET':
      return initialState

    case 'SEED_HISTORY':
      // Always prefer the more complete dataset. The REST history endpoint is
      // the source of truth; if it has more plays than what SSE delivered so
      // far (e.g. user opened the page mid-replay), use it so the chart starts
      // from play 1 rather than from whenever the browser connected.
      if (action.payload.length <= state.wpHistory.length) return state
      return {
        ...state,
        wpHistory: action.payload,
        replayComplete: action.payload.length > 0,
      }

    case 'SSE_EVENT': {
      const event = action.payload

      if (event.event_type === 'play_update') {
        const point: WpDataPoint = {
          sequence: event.play.sequence,
          playId: event.play.id,
          homeWp: event.home_wp,
          awayWp: event.away_wp,
          description: event.play.description,
          quarter: event.play.quarter,
          gameClock: event.play.game_clock_seconds,
          scoreHome: event.play.score_home,
          scoreAway: event.play.score_away,
          topShap: event.top_shap,
          down: event.play.down,
          yardsToGo: event.play.yards_to_go,
          yardLineFromOwn: event.play.yard_line_from_own,
          playType: event.play.play_type,
          posteamAbbr: event.play.posteam_abbr,
        }
        return {
          ...state,
          connectionState: 'open',
          lastEventAt: Date.now(),
          wpHistory: [...state.wpHistory, point],
        }
      }

      if (event.event_type === 'replay_complete') {
        return { ...state, replayComplete: true }
      }

      return { ...state, lastEventAt: Date.now() }
    }

    default:
      return state
  }
}
