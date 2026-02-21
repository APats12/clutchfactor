import type { Play } from './play'
import type { ShapFeature } from './prediction'
import type { GameStatus } from './game'

export interface PlayUpdateEvent {
  event_type: 'play_update'
  game_id: string
  play: Play
  home_wp: number
  away_wp: number
  top_shap: ShapFeature[]
}

export interface GameStatusEvent {
  event_type: 'game_status'
  game_id: string
  status: GameStatus
  home_score: number
  away_score: number
}

export interface ReplayCompleteEvent {
  event_type: 'replay_complete'
  game_id: string
}

export type SSEEvent = PlayUpdateEvent | GameStatusEvent | ReplayCompleteEvent
