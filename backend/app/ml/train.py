"""
ClutchFactor ML training script.

Usage:
    uv run python -m app.ml.train [--seasons 2016 2017 ... 2022] [--eval-season 2023]

Downloads nflfastR play-by-play CSVs if not present, trains an XGBoost classifier,
evaluates on a held-out season, saves the artifact, and registers it in the database.
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.isotonic import IsotonicRegression
from xgboost import XGBClassifier

from app.config import get_settings
from app.ml.calibration import _CalibratedModel
from app.ml.evaluate import compute_metrics
from app.ml.features import FEATURE_COLS, FILL_VALUES, build_feature_matrix

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parents[3] / "ml" / "data"
ARTIFACT_DIR = Path(__file__).parents[3] / "ml" / "artifacts"
NFLVERSE_BASE = "https://github.com/nflverse/nflverse-data/releases/download/pbp"

# Play types to keep (exclude non-football rows)
VALID_PLAY_TYPES = {"pass", "run", "field_goal", "punt", "extra_point", "kickoff", "no_play"}


def download_season(season: int) -> Path:
    """Download a single season's play-by-play CSV. Returns path to decompressed CSV."""
    import gzip
    import shutil

    import httpx
    from tqdm import tqdm

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = DATA_DIR / f"play_by_play_{season}.csv"
    gz_path = DATA_DIR / f"play_by_play_{season}.csv.gz"

    if csv_path.exists():
        logger.info("Season %d already downloaded, skipping.", season)
        return csv_path

    url = f"{NFLVERSE_BASE}/play_by_play_{season}.csv.gz"
    logger.info("Downloading %s ...", url)

    with httpx.stream("GET", url, follow_redirects=True, timeout=300) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        with open(gz_path, "wb") as f, tqdm(total=total, unit="B", unit_scale=True) as bar:
            for chunk in r.iter_bytes(chunk_size=65536):
                f.write(chunk)
                bar.update(len(chunk))

    logger.info("Decompressing %s ...", gz_path)
    with gzip.open(gz_path, "rb") as f_in, open(csv_path, "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)
    gz_path.unlink()

    return csv_path


def load_season(season: int) -> pd.DataFrame:
    csv_path = DATA_DIR / f"play_by_play_{season}.csv"
    if not csv_path.exists():
        raise FileNotFoundError(
            f"Season {season} CSV not found at {csv_path}. Run `make download-data` first."
        )
    df = pd.read_csv(csv_path, low_memory=False)
    df["season"] = season
    return df


def prepare_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter and prepare the raw nflfastR DataFrame for training.

    - Keep only plays where result is not null (complete games)
    - Keep only plays with valid play types
    - Create target column: home_team_wins = (result > 0)
    - Compute features consistent with inference-time GameState
    """
    # result = home_score - away_score at end of game (nflfastR convention)
    df = df[df["result"].notna()].copy()

    # Filter play types
    df = df[df["play_type"].isin(VALID_PLAY_TYPES)].copy()

    # ── Column aliases ────────────────────────────────────────────────────────
    if "ydstogo" in df.columns and "yards_to_go" not in df.columns:
        df["yards_to_go"] = df["ydstogo"]

    # score_differential: always home_score - away_score (home perspective).
    # nflfastR's native score_differential is posteam-perspective — do NOT use it.
    df["score_differential"] = (
        df["total_home_score"].fillna(0) - df["total_away_score"].fillna(0)
    )

    # ── Possession features ───────────────────────────────────────────────────
    # posteam_is_home: 1 if the team with possession is the home team
    if "posteam" in df.columns and "home_team" in df.columns:
        df["posteam_is_home"] = (df["posteam"] == df["home_team"]).astype(float)
    else:
        df["posteam_is_home"] = 0.5  # unknown

    # receive_2h_ko: 1 if possession team will receive the 2nd-half kickoff.
    # Formula: home_opening_kickoff XOR posteam_is_home
    if "home_opening_kickoff" in df.columns:
        hok = df["home_opening_kickoff"].fillna(0).astype(int)
        pih = df["posteam_is_home"].fillna(0).astype(int)
        df["receive_2h_ko"] = (hok != pih).astype(float)
    else:
        df["receive_2h_ko"] = 0.0

    # ── Target ────────────────────────────────────────────────────────────────
    df["target"] = (df["result"] > 0).astype(int)

    # ── Keep required columns ─────────────────────────────────────────────────
    # Note: spread_time and diff_time_ratio are computed by build_feature_matrix()
    # Keep qtr as a diagnostic column for per-quarter calibration reports.
    raw_feature_cols = [c for c in FEATURE_COLS if c not in ("spread_time", "diff_time_ratio")]
    needed = raw_feature_cols + ["target", "season", "game_id", "qtr"]
    available = [c for c in needed if c in df.columns]
    df = df[available].copy()

    # Coerce to numeric
    for col in raw_feature_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


async def register_model_version(
    name: str,
    artifact_path: str,
    brier_score: float,
    log_loss_val: float,
    trained_on_seasons: list[str],
) -> None:
    from sqlalchemy import update
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from app.db.models.model_version import ModelVersion

    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with factory() as session:
        # Set all existing versions to is_current=False
        await session.execute(
            update(ModelVersion).values(is_current=False)
        )
        # Insert new version
        mv = ModelVersion(
            id=uuid.uuid4(),
            name=name,
            artifact_path=artifact_path,
            brier_score=brier_score,
            log_loss_val=log_loss_val,
            trained_on_seasons=trained_on_seasons,
            is_current=True,
        )
        session.add(mv)
        await session.commit()
        logger.info("Registered model version '%s' in database.", name)

    await engine.dispose()


def _calibration_report(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    qtr: np.ndarray | None,
    label: str,
) -> None:
    """Print overall + per-quarter calibration summary."""
    metrics = compute_metrics(y_true, y_prob)
    frac, mean_pred = calibration_curve(y_true, y_prob, n_bins=10)
    max_gap = float(np.max(np.abs(frac - mean_pred)))
    print(f"\n  [{label}]  Brier={metrics['brier_score']:.4f}  LogLoss={metrics['log_loss']:.4f}  MaxCalibGap={max_gap:.3f}")

    if qtr is not None:
        for q in sorted(np.unique(qtr)):
            mask = qtr == q
            if mask.sum() < 50:
                continue
            fq, mq = calibration_curve(y_true[mask], y_prob[mask], n_bins=8)
            gap_q = float(np.max(np.abs(fq - mq)))
            brier_q = float(np.mean((y_prob[mask] - y_true[mask]) ** 2))
            label_q = f"Q{int(q)}" if q <= 4 else "OT"
            print(f"    {label_q}: n={mask.sum():5d}  Brier={brier_q:.4f}  MaxCalibGap={gap_q:.3f}")


def train(
    seasons: list[int],
    calib_season: int,
    eval_season: int,
    skip_download: bool = False,
) -> None:
    # Download seasons if needed
    if not skip_download:
        all_seasons = list(set(seasons + [calib_season, eval_season]))
        for s in all_seasons:
            try:
                download_season(s)
            except Exception as exc:
                logger.warning("Could not download season %d: %s", s, exc)

    # Load and concatenate all needed seasons
    logger.info("Loading seasons: train=%s  calib=%d  eval=%d", seasons, calib_season, eval_season)
    dfs = []
    for s in list(set(seasons + [calib_season, eval_season])):
        try:
            dfs.append(load_season(s))
        except FileNotFoundError as exc:
            logger.warning(str(exc))

    if not dfs:
        raise RuntimeError("No data loaded. Run `make download-data` first.")

    raw = pd.concat(dfs, ignore_index=True)
    df = prepare_dataset(raw)

    if "target" not in df.columns:
        raise RuntimeError("Dataset preparation failed — 'target' column missing.")

    # ── Season splits ─────────────────────────────────────────────────────────
    train_mask = df["season"].isin(seasons)
    calib_mask = df["season"] == calib_season
    eval_mask = df["season"] == eval_season

    X_train = build_feature_matrix(df[train_mask])
    y_train = df[train_mask]["target"].values

    X_calib = build_feature_matrix(df[calib_mask])
    y_calib = df[calib_mask]["target"].values

    X_eval = build_feature_matrix(df[eval_mask])
    y_eval = df[eval_mask]["target"].values
    qtr_eval = df[eval_mask]["qtr"].values if "qtr" in df.columns else None

    logger.info(
        "Train rows: %d  Calib rows: %d  Eval rows: %d",
        len(X_train), len(X_calib), len(X_eval),
    )

    # ── Train XGBoost ─────────────────────────────────────────────────────────
    model = XGBClassifier(
        n_estimators=500,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        use_label_encoder=False,
        eval_metric="logloss",
        early_stopping_rounds=20,
        tree_method="hist",
        random_state=42,
    )

    logger.info("Training XGBoost model...")
    model.fit(
        X_train,
        y_train,
        eval_set=[(X_eval, y_eval)],
        verbose=50,
    )

    # ── Evaluation ────────────────────────────────────────────────────────────
    raw_probs = model.predict_proba(X_eval)[:, 1]

    print("\n── Evaluation report (eval season) ───────────────────────────────")
    _calibration_report(y_eval, raw_probs, qtr_eval, "Raw XGBoost")
    print("──────────────────────────────────────────────────────────────────")

    # ── Save artifact ─────────────────────────────────────────────────────────
    # Save the raw XGBClassifier via joblib. Isotonic calibration was removed
    # because IsotonicRegression creates a step function that collapses many
    # consecutive plays to the same WP value, making the chart appear flat.
    # Raw XGBoost also scores better on Brier and LogLoss for this dataset.
    artifact_dir = Path(get_settings().model_artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
    name = f"xgb_{timestamp}"
    artifact_path = artifact_dir / f"{name}.joblib"
    joblib.dump(model, str(artifact_path))
    logger.info("Saved model artifact: %s", artifact_path)

    raw_metrics = compute_metrics(y_eval, raw_probs)

    asyncio.run(
        register_model_version(
            name=name,
            artifact_path=artifact_path.name,
            brier_score=raw_metrics["brier_score"],
            log_loss_val=raw_metrics["log_loss"],
            trained_on_seasons=[str(s) for s in seasons],
        )
    )

    print(f"\n✓ Training complete.")
    print(f"  Model: {name}")
    print(f"  Artifact: {artifact_path}")
    print(f"  Brier score: {raw_metrics['brier_score']:.4f}")
    print(f"  Log loss:    {raw_metrics['log_loss']:.4f}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description="Train ClutchFactor win-probability model")
    parser.add_argument(
        "--seasons",
        nargs="+",
        type=int,
        default=list(range(2016, 2022)),
        help="XGBoost training seasons (default: 2016–2021)",
    )
    parser.add_argument(
        "--calib-season",
        type=int,
        default=2022,
        help="Season used to fit isotonic calibration (default: 2022)",
    )
    parser.add_argument(
        "--eval-season",
        type=int,
        default=2023,
        help="Held-out evaluation season (default: 2023)",
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Skip downloading CSVs (assume already present)",
    )
    args = parser.parse_args()
    train(
        seasons=args.seasons,
        calib_season=args.calib_season,
        eval_season=args.eval_season,
        skip_download=args.skip_download,
    )
