"""
SSE Connection Manager.

Maintains one asyncio.Queue per connected browser tab per game.
The module-level singleton `sse_manager` is shared between:
  - app/api/stream.py  (subscribes/unsubscribes clients)
  - app/services/replay_service.py  (broadcasts events)
"""
from __future__ import annotations

import asyncio
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class SSEConnectionManager:
    def __init__(self) -> None:
        # game_id → list of asyncio.Queue
        self._queues: dict[str, list[asyncio.Queue]] = defaultdict(list)

    async def subscribe(self, game_id: str) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=200)
        self._queues[game_id].append(q)
        logger.debug("SSE subscriber added for game %s (total: %d)", game_id, len(self._queues[game_id]))
        return q

    async def unsubscribe(self, game_id: str, q: asyncio.Queue) -> None:
        try:
            self._queues[game_id].remove(q)
            logger.debug("SSE subscriber removed for game %s (remaining: %d)", game_id, len(self._queues[game_id]))
        except ValueError:
            pass  # Already removed

    async def broadcast(self, game_id: str, event: dict) -> None:
        queues = list(self._queues.get(game_id, []))
        for q in queues:
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                logger.warning("SSE queue full for game %s — dropping event", game_id)

    def subscriber_count(self, game_id: str) -> int:
        return len(self._queues.get(game_id, []))


# Module-level singleton
sse_manager = SSEConnectionManager()
