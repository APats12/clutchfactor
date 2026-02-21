"""
ReplayService

Orchestrates a full replay session for one game:
  DeveloperReplayAdapter.stream_plays()
    → Persist Play + PlayRaw rows
    → extract_features()
    → PredictionService.predict_raw()
    → Persist WpPrediction
    → ShapService.explain()
    → Persist ShapValue rows
    → SSEConnectionManager.broadcast(PlayUpdateEvent)
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from app.db.base import get_session_factory
from app.db.models.play import Play
from app.db.models.play_raw import PlayRaw
from app.db.models.shap_value import ShapValue
from app.db.models.wp_prediction import WpPrediction
from app.ml.features import extract_features
from app.ml.registry import get_current
from app.providers.developer_replay import DeveloperReplayAdapter
from app.schemas.play import PlayRead
from app.schemas.sse import PlayUpdateEvent, ReplayCompleteEvent
from app.services.prediction_service import PredictionService
from app.services.shap_service import ShapService
from app.services.sse_manager import sse_manager
from app.utils.cache import set_latest_game_event

logger = logging.getLogger(__name__)


class ReplayService:
    def __init__(
        self,
        adapter: DeveloperReplayAdapter,
        prediction_service: PredictionService,
        shap_service: ShapService,
    ) -> None:
        self._adapter = adapter
        self._pred_svc = prediction_service
        self._shap_svc = shap_service

    async def run(self, game_id: str) -> None:
        """
        Main replay loop. Runs as an asyncio.Task.
        Processes plays one at a time; each iteration yields to the event loop
        via the adapter's asyncio.sleep.

        Creates its own DB session so the session lifetime matches the task
        lifetime (not the HTTP request that spawned us).
        """
        logger.info("Replay started for game %s", game_id)

        try:
            model, version_id, version_name = await get_current()
        except RuntimeError as exc:
            logger.error("Cannot start replay — model not available: %s", exc)
            return

        factory = get_session_factory()
        play_count = 0

        async with factory() as db:
            async for gs in self._adapter.stream_plays(game_id):
                try:
                    # 1. Persist Play row
                    play_id = uuid.uuid4()
                    play = Play(
                        id=play_id,
                        game_id=uuid.UUID(game_id) if len(game_id) == 36 else uuid.uuid4(),
                        play_number=gs.get("play_number", play_count + 1),
                        sequence=gs.get("sequence", play_count),
                        quarter=gs.get("quarter", 1),
                        game_clock_seconds=gs.get("game_clock_seconds", 0),
                        down=gs.get("down"),
                        yards_to_go=gs.get("yards_to_go"),
                        yard_line_from_own=gs.get("yard_line_from_own"),
                        posteam_abbr=gs.get("posteam_abbr"),
                        score_home=gs.get("score_home", 0),
                        score_away=gs.get("score_away", 0),
                        play_type=gs.get("play_type"),
                        description=gs.get("description"),
                    )

                    # 2. Persist PlayRaw row
                    raw_payload = {k: v for k, v in gs.get("raw_payload", {}).items() if _is_json_serialisable(v)}
                    play_raw = PlayRaw(
                        id=uuid.uuid4(),
                        play_id=play_id,
                        provider="developer_replay",
                        payload=raw_payload,
                    )

                    db.add(play)
                    db.add(play_raw)
                    await db.flush()  # get IDs without full commit

                    # 3. Extract features
                    features = extract_features(dict(gs))

                    # 4. Predict
                    home_wp, away_wp = await self._pred_svc.predict_raw(features, model)

                    # Clamp to certainty only when the game clock has fully expired.
                    # Do NOT clamp early (e.g. ≤10s) — the model's gradual decline is
                    # correct and matches how ESPN/nflfastR display end-game WP.
                    game_secs = gs.get("game_seconds_remaining") or 0
                    score_diff = gs.get("score_differential", 0) or 0
                    quarter = gs.get("quarter", 1) or 1
                    # Only clamp in Q4/OT at 0:00 — quarter-end rows in Q1–Q3 also
                    # have game_clock_seconds=0 but the game is not over.
                    if game_secs == 0 and quarter >= 4 and score_diff != 0:
                        if score_diff > 0:
                            home_wp, away_wp = 1.0, 0.0
                        else:
                            home_wp, away_wp = 0.0, 1.0
                        # score_diff == 0 at 0:00 Q4 → OT, don't clamp

                    # 5. Persist WpPrediction
                    wp_pred = WpPrediction(
                        id=uuid.uuid4(),
                        play_id=play_id,
                        model_version_id=version_id,
                        home_wp=home_wp,
                        away_wp=away_wp,
                    )
                    db.add(wp_pred)
                    await db.flush()

                    # 6. SHAP explanation (synchronous, < 10ms)
                    top_shap = self._shap_svc.explain(features, model, top_n=5)

                    # 7. Persist ShapValues
                    for sf in top_shap:
                        db.add(ShapValue(
                            id=uuid.uuid4(),
                            wp_prediction_id=wp_pred.id,
                            feature_name=sf.feature_name,
                            shap_value=sf.shap_value,
                        ))

                    await db.commit()

                    # 8. Build and broadcast SSE event
                    play_read = PlayRead(
                        id=play.id,
                        game_id=play.game_id,
                        play_number=play.play_number,
                        sequence=play.sequence,
                        quarter=play.quarter,
                        game_clock_seconds=play.game_clock_seconds,
                        down=play.down,
                        yards_to_go=play.yards_to_go,
                        yard_line_from_own=play.yard_line_from_own,
                        score_home=play.score_home,
                        score_away=play.score_away,
                        play_type=play.play_type,
                        description=play.description,
                        posteam_abbr=gs.get("posteam_abbr"),
                        created_at=datetime.now(tz=timezone.utc),
                    )

                    event = PlayUpdateEvent(
                        game_id=game_id,
                        play=play_read,
                        home_wp=home_wp,
                        away_wp=away_wp,
                        top_shap=top_shap,
                    )
                    event_dict = event.model_dump(mode="json")
                    await sse_manager.broadcast(game_id, event_dict)
                    await set_latest_game_event(game_id, event_dict)

                    play_count += 1

                except Exception:
                    logger.exception("Error processing play %d for game %s", play_count, game_id)
                    await db.rollback()
                    continue

        # Broadcast completion
        complete_event = ReplayCompleteEvent(game_id=game_id).model_dump(mode="json")
        await sse_manager.broadcast(game_id, complete_event)
        logger.info("Replay complete for game %s (%d plays processed)", game_id, play_count)


def _is_json_serialisable(val) -> bool:
    """Filter out non-JSON-serialisable values from the raw payload."""
    import math
    if val is None:
        return True
    if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
        return False
    if isinstance(val, (str, int, bool, list, dict)):
        return True
    try:
        import json
        json.dumps(val)
        return True
    except (TypeError, ValueError):
        return False
