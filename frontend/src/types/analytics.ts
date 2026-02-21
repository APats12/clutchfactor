// Analytics types matching the backend app/schemas/analytics.py models

export interface PlayRef {
  play_id: string
  sequence: number
  quarter: number
  game_clock_seconds: number
  description: string | null
}

// -----------------------------------------------------------------------
// Momentum Swings
// -----------------------------------------------------------------------

export interface MomentumSwing {
  rank: number
  play_ref: PlayRef
  wp_before: number
  wp_after: number
  delta_wp: number
  magnitude: number
  tag: string | null
  is_turning_point: boolean
}

export interface MomentumSwingsResponse {
  game_id: string
  swings: MomentumSwing[]
}

// -----------------------------------------------------------------------
// Clutch Index
// -----------------------------------------------------------------------

export interface ClutchPlay {
  rank: number
  play_ref: PlayRef
  delta_wp: number
  clutch_score: number
  time_factor: number
  close_factor: number
  score_diff: number
}

export interface ClutchDrive {
  drive_number: number
  posteam_abbr: string | null
  clutch_total: number
  play_count: number
}

export interface ClutchTeamTotals {
  offense: number
  defense: number
}

export interface ClutchResponse {
  game_id: string
  top_plays: ClutchPlay[]
  top_drives: ClutchDrive[]
  team_totals: {
    home: ClutchTeamTotals
    away: ClutchTeamTotals
  }
}

// -----------------------------------------------------------------------
// Coach Decision Grades
// -----------------------------------------------------------------------

export interface DecisionOption {
  wp: number
  detail: string | null
}

export type DecisionType = 'go_for_it' | 'punt' | 'field_goal'
export type GradeLabel = 'Optimal' | 'Questionable' | 'Bad' | 'Very Bad'

export interface CoachDecision {
  play_ref: PlayRef
  situation: string
  actual_type: DecisionType
  actual_wp_after: number
  alternatives: Record<string, DecisionOption | null>
  best_action: string
  decision_delta: number
  grade: GradeLabel
  grade_emoji: string
}

export interface DecisionGradesResponse {
  game_id: string
  decisions: CoachDecision[]
}
