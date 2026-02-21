export type GameStatus = 'scheduled' | 'in_progress' | 'final'

export interface Team {
  id: string
  abbr: string
  name: string
  conference: string | null
  division: string | null
  logo_url: string | null
  primary_color: string | null
  secondary_color: string | null
}

export interface Game {
  id: string
  season: number
  week: number
  home_team: Team
  away_team: Team
  status: GameStatus
  nflfastr_game_id: string | null
  scheduled_at: string | null
  started_at: string | null
  final_home_score: number | null
  final_away_score: number | null
  venue: string | null
  home_wp: number | null
  away_wp: number | null
}

export interface GameDetail extends Game {
  play_count: number
}
