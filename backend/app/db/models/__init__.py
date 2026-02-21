# Re-export all models so Alembic env.py can import Base and pick up metadata
from app.db.models.game import Game, GameStatus
from app.db.models.model_version import ModelVersion
from app.db.models.odds_snapshot import OddsSnapshot
from app.db.models.play import Play
from app.db.models.play_raw import PlayRaw
from app.db.models.shap_value import ShapValue
from app.db.models.snapshot import GameStateSnapshot
from app.db.models.team import Team
from app.db.models.wp_prediction import WpPrediction

__all__ = [
    "Team",
    "Game",
    "GameStatus",
    "Play",
    "PlayRaw",
    "GameStateSnapshot",
    "ModelVersion",
    "WpPrediction",
    "ShapValue",
    "OddsSnapshot",
]
