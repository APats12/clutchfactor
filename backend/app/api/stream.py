from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.services.sse_manager import sse_manager
from app.utils.cache import get_latest_game_event

router = APIRouter(tags=["stream"])


@router.get("/stream/games/{game_id}")
async def stream_game(game_id: str, request: Request) -> StreamingResponse:
    async def event_generator():
        # Send cached latest event immediately so new subscribers see current state
        cached = await get_latest_game_event(game_id)
        if cached:
            yield f"data: {cached}\n\n"

        q = await sse_manager.subscribe(game_id)
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event = await asyncio.wait_for(q.get(), timeout=15.0)
                    yield f"data: {json.dumps(event)}\n\n"
                except asyncio.TimeoutError:
                    # Keep-alive heartbeat
                    yield ": heartbeat\n\n"
        finally:
            await sse_manager.unsubscribe(game_id, q)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
