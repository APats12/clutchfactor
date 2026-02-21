"""
Standalone script to download nflfastR play-by-play CSVs from nflverse GitHub releases.

Usage:
    python ml/scripts/download_pbp.py [--seasons 2016 2017 ... 2023]

Files are saved to ml/data/ and decompressed.
"""
from __future__ import annotations

import argparse
import gzip
import logging
import shutil
import sys
from pathlib import Path

# Allow running from repo root
sys.path.insert(0, str(Path(__file__).parents[2] / "backend"))

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parents[1] / "data"
NFLVERSE_BASE = "https://github.com/nflverse/nflverse-data/releases/download/pbp"


def download_season(season: int) -> None:
    try:
        import httpx
        from tqdm import tqdm
    except ImportError:
        logger.error("Missing dependencies. Run: uv pip install httpx tqdm")
        sys.exit(1)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = DATA_DIR / f"play_by_play_{season}.csv"
    gz_path = DATA_DIR / f"play_by_play_{season}.csv.gz"

    if csv_path.exists():
        logger.info("Season %d: already exists at %s, skipping.", season, csv_path)
        return

    url = f"{NFLVERSE_BASE}/play_by_play_{season}.csv.gz"
    logger.info("Season %d: downloading from %s", season, url)

    try:
        with httpx.stream("GET", url, follow_redirects=True, timeout=300) as r:
            r.raise_for_status()
            total = int(r.headers.get("content-length", 0))
            with (
                open(gz_path, "wb") as f,
                tqdm(total=total, unit="B", unit_scale=True, desc=f"{season}") as bar,
            ):
                for chunk in r.iter_bytes(chunk_size=65536):
                    f.write(chunk)
                    bar.update(len(chunk))
    except httpx.HTTPError as exc:
        logger.error("Download failed for season %d: %s", season, exc)
        if gz_path.exists():
            gz_path.unlink()
        return

    logger.info("Season %d: decompressing...", season)
    with gzip.open(gz_path, "rb") as f_in, open(csv_path, "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)
    gz_path.unlink()
    logger.info("Season %d: saved to %s (%.1f MB)", season, csv_path, csv_path.stat().st_size / 1e6)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download nflfastR play-by-play data")
    parser.add_argument(
        "--seasons",
        nargs="+",
        type=int,
        default=list(range(2016, 2024)),
        help="Seasons to download (default: 2016–2023)",
    )
    args = parser.parse_args()

    for season in args.seasons:
        download_season(season)

    logger.info("Done. CSVs in %s", DATA_DIR)
