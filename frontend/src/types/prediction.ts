export interface ShapFeature {
  feature_name: string
  shap_value: number
  direction: 'positive' | 'negative'
  display_name: string
}

export interface WpPrediction {
  play_id: string
  home_wp: number
  away_wp: number
  model_version: string
  top_shap: ShapFeature[]
  predicted_at: string
}

export interface WpDataPoint {
  sequence: number
  playId?: string
  homeWp: number
  awayWp: number
  description: string | null
  quarter: number
  gameClock: number
  scoreHome: number
  scoreAway: number
  topShap: ShapFeature[]
  // situational fields (available from wp-history endpoint)
  down?: number | null
  yardsToGo?: number | null
  yardLineFromOwn?: number | null
  playType?: string | null
  posteamAbbr?: string | null
}
