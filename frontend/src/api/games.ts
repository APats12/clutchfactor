import client from './client'
import type { Game, GameDetail } from '../types/game'
import type { Play } from '../types/play'
import type { WpDataPoint } from '../types/prediction'
import type { ShapFeature } from '../types/prediction'
import type {
  MomentumSwingsResponse,
  ClutchResponse,
  DecisionGradesResponse,
} from '../types/analytics'

export async function fetchGames(params?: {
  date?: string
  status?: string
  season?: number
  week?: number
  playoffs?: boolean
}): Promise<Game[]> {
  const { data } = await client.get<Game[]>('/games', { params })
  return data
}

export async function fetchGame(id: string): Promise<GameDetail> {
  const { data } = await client.get<GameDetail>(`/games/${id}`)
  return data
}

export async function fetchPlays(gameId: string): Promise<Play[]> {
  const { data } = await client.get<Play[]>(`/games/${gameId}/plays`)
  return data
}

// Shape returned by the backend PlayWpRead schema
interface PlayWpRead {
  id: string
  sequence: number
  home_wp: number
  away_wp: number
  description: string | null
  quarter: number
  game_clock_seconds: number
  score_home: number
  score_away: number
  top_shap: ShapFeature[]
  down: number | null
  yards_to_go: number | null
  yard_line_from_own: number | null
  play_type: string | null
  posteam_abbr: string | null
}

export async function fetchWpHistory(gameId: string): Promise<WpDataPoint[]> {
  const { data } = await client.get<PlayWpRead[]>(`/games/${gameId}/wp-history`)
  return data.map((p) => ({
    sequence: p.sequence,
    playId: p.id,
    homeWp: p.home_wp,
    awayWp: p.away_wp,
    description: p.description,
    quarter: p.quarter,
    gameClock: p.game_clock_seconds,
    scoreHome: p.score_home,
    scoreAway: p.score_away,
    topShap: p.top_shap,
    down: p.down,
    yardsToGo: p.yards_to_go,
    yardLineFromOwn: p.yard_line_from_own,
    playType: p.play_type,
    posteamAbbr: p.posteam_abbr,
  }))
}

export async function fetchMomentumSwings(
  gameId: string,
  top = 3,
): Promise<MomentumSwingsResponse> {
  const { data } = await client.get<MomentumSwingsResponse>(
    `/games/${gameId}/momentum-swings`,
    { params: { top } },
  )
  return data
}

export async function fetchClutchIndex(
  gameId: string,
  top = 5,
): Promise<ClutchResponse> {
  const { data } = await client.get<ClutchResponse>(`/games/${gameId}/clutch`, {
    params: { top },
  })
  return data
}

export async function fetchDecisionGrades(
  gameId: string,
  top = 10,
): Promise<DecisionGradesResponse> {
  const { data } = await client.get<DecisionGradesResponse>(
    `/games/${gameId}/decision-grades`,
    { params: { top } },
  )
  return data
}
