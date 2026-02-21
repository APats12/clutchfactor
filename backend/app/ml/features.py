from __future__ import annotations

import numpy as np
import pandas as pd

# Feature columns fed to the XGBoost model — ORDER MATTERS.
# Do not reorder without retraining the model.
#
# Derived features (spread_time, diff_time_ratio) are computed at runtime
# by extract_features() and build_feature_matrix(); they are NOT raw inputs.
FEATURE_COLS = [
    "down",
    "yards_to_go",
    "yardline_100",             # distance from opponent end zone (1–99)
    "game_seconds_remaining",
    "half_seconds_remaining",
    "score_differential",       # home_score - away_score (always home perspective)
    "posteam_is_home",          # 1 if possession team is home team, else 0
    "posteam_timeouts_remaining",
    "defteam_timeouts_remaining",
    "receive_2h_ko",            # 1 if possession team receives 2nd-half kickoff
    "spread_line",              # Vegas pre-game spread (positive = home favored)
    "spread_time",              # derived: spread_line * game_seconds_remaining / 3600
    "diff_time_ratio",          # derived: score_differential * (1 - game_seconds_remaining / 3600)
    "ep",                       # expected points for current possession (changes every play)
]

# Fill values for NaN features (safe defaults, not imputed from training data)
FILL_VALUES: dict[str, float] = {
    "down": 0.0,                        # 0 = no scrimmage play (kickoff, PAT, etc.)
    "yards_to_go": 10.0,
    "yardline_100": 50.0,
    "game_seconds_remaining": 3600.0,
    "half_seconds_remaining": 1800.0,
    "score_differential": 0.0,
    "posteam_is_home": 0.5,             # unknown possession team
    "posteam_timeouts_remaining": 3.0,
    "defteam_timeouts_remaining": 3.0,
    "receive_2h_ko": 0.0,
    "spread_line": 0.0,
    "spread_time": 0.0,
    "diff_time_ratio": 0.0,
    "ep": 0.0,                          # neutral EP for non-standard plays
}

# Human-readable labels shown in the SHAP panel
FEATURE_DISPLAY_NAMES: dict[str, str] = {
    "down": "Down",
    "yards_to_go": "Yards to Go",
    "yardline_100": "Field Position",
    "game_seconds_remaining": "Time Remaining",
    "half_seconds_remaining": "Half Time Remaining",
    "score_differential": "Score Differential",
    "posteam_is_home": "Possession (Home)",
    "posteam_timeouts_remaining": "Offense Timeouts",
    "defteam_timeouts_remaining": "Defense Timeouts",
    "receive_2h_ko": "Receives 2nd-Half Kickoff",
    "spread_line": "Pre-game Spread",
    "spread_time": "Spread × Time Remaining",
    "diff_time_ratio": "Lead × Time Elapsed",
    "ep": "Expected Points",
}


def _fill(val, default: float) -> float:
    """Return val as float, or default if None/NaN."""
    if val is None:
        return default
    try:
        v = float(val)
        return default if np.isnan(v) else v
    except (TypeError, ValueError):
        return default


def extract_features(play: dict) -> np.ndarray:
    """
    Convert a play dict (GameState or nflfastR row) to a (1, N) float32 array.

    Accepts both raw nflfastR column names and our normalised GameState keys.
    Computes derived features (spread_time, diff_time_ratio) inline.
    Returns shape (1, len(FEATURE_COLS)).
    """
    def _get(key: str) -> float:
        return _fill(play.get(key), FILL_VALUES[key])

    # Raw values needed for derived features
    game_secs = _get("game_seconds_remaining")
    spread = _get("spread_line")
    score_diff = _get("score_differential")

    # Derived features
    spread_time = spread * (game_secs / 3600.0)
    diff_time_ratio = score_diff * (1.0 - game_secs / 3600.0)

    augmented = {
        **play,
        "spread_time": spread_time,
        "diff_time_ratio": diff_time_ratio,
    }

    def _get2(key: str) -> float:
        return _fill(augmented.get(key), FILL_VALUES[key])

    features = [_get2(col) for col in FEATURE_COLS]
    return np.array([features], dtype=np.float32)


def build_feature_matrix(df: pd.DataFrame) -> np.ndarray:
    """
    Convert a DataFrame (nflfastR play-by-play) to a feature matrix.
    Applies fill values for NaN entries and computes derived features.
    """
    df = df.copy()

    # Fill raw columns first so derived features use clean values
    for col in ["game_seconds_remaining", "spread_line", "score_differential"]:
        if col in df.columns:
            df[col] = df[col].fillna(FILL_VALUES[col])

    # Compute derived features
    game_secs = df["game_seconds_remaining"]
    df["spread_time"] = df["spread_line"] * (game_secs / 3600.0)
    df["diff_time_ratio"] = df["score_differential"] * (1.0 - game_secs / 3600.0)

    subset = df[FEATURE_COLS].copy()
    for col, fill in FILL_VALUES.items():
        if col in subset.columns:
            subset[col] = subset[col].fillna(fill)

    return subset.values.astype(np.float32)
