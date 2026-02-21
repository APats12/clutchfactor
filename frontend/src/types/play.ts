export interface Play {
  id: string
  game_id: string
  play_number: number
  sequence: number
  quarter: number
  game_clock_seconds: number
  down: number | null
  yards_to_go: number | null
  yard_line_from_own: number | null
  score_home: number
  score_away: number
  play_type: string | null
  description: string | null
  posteam_abbr: string | null
  created_at: string
}
