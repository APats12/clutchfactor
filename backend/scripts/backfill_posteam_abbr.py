"""
One-shot backfill: populate plays.posteam_abbr from the description column.

nflfastR descriptions begin with either:
  "(MM:SS) ABBR ..."   — play descriptions with a clock prefix
  "ABBR ..."           — some special plays
  "Timeout #N by ABBR" — timeout plays

We extract the first token after the optional clock prefix.
"""
from __future__ import annotations
import asyncio
import re
from sqlalchemy import select, update
from app.db.base import init_db, get_session_factory
from app.config import get_settings
from app.db.models.play import Play
from app.db.models.game import Game
from app.db.models.team import Team

CLOCK_PREFIX = re.compile(r'^\(\d+:\d+\)\s*(?:\([\w\s]+\)\s*)?')
TIMEOUT_RE   = re.compile(r'Timeout #\d+ by (\w+)')
ABBR_RE      = re.compile(r'^([A-Z]{2,3})\b')


def _extract_abbr(description: str | None) -> str | None:
    if not description:
        return None
    # Timeout play
    m = TIMEOUT_RE.match(description)
    if m:
        return m.group(1)
    # Strip leading clock "(MM:SS) " and optional formation "(Shotgun) "
    stripped = CLOCK_PREFIX.sub('', description).strip()
    m = ABBR_RE.match(stripped)
    if m:
        return m.group(1)
    return None


async def main() -> None:
    settings = get_settings()
    init_db(settings.database_url)
    factory = get_session_factory()

    async with factory() as db:
        # Load all plays that don't yet have posteam_abbr set
        result = await db.execute(
            select(Play).where(Play.posteam_abbr.is_(None))
        )
        plays = result.scalars().all()
        print(f"Found {len(plays)} plays missing posteam_abbr")

        updated = 0
        for play in plays:
            abbr = _extract_abbr(play.description)
            if abbr:
                play.posteam_abbr = abbr
                updated += 1

        await db.commit()
        print(f"Backfilled {updated} plays")

        # Spot-check
        result2 = await db.execute(
            select(Play).order_by(Play.sequence).limit(10)
        )
        for p in result2.scalars().all():
            print(f"  seq={p.sequence} Q{p.quarter} posteam={p.posteam_abbr!r:6} | {str(p.description)[:50]}")


if __name__ == "__main__":
    asyncio.run(main())
