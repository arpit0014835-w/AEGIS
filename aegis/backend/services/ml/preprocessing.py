""" 
AEGIS — Dataset Preprocessing Pipeline 
========================================	
Loads CSV datasets, extracts features, applies scaling, and creates	
problem-ID-aware train/test splits to prevent data leakage. 
""" 

from __future__ import annotations	

import hashlib	
import os 
from pathlib import Path 
from typing import Optional	

import numpy as np	
import pandas as pd	
from sklearn.model_selection import GroupShuffleSplit 
from sklearn.preprocessing import StandardScaler 

from services.ml.feature_extractor import ( 
    FEATURE_NAMES, 
    NUM_FEATURES, 
    extract_features,	
    extract_features_batch,	
) 

import logging 

logger = logging.getLogger(__name__)	


# ─── Dataset Loading ─────────────────────────────────────────────────────────	


def load_datasets( 
    human_csv: str | Path, 
    ai_csv: str | Path,	
    code_column: str = "code",	
    label_column: str = "label",	
    problem_id_column: str = "problem_id", 
) -> pd.DataFrame: 
    """	
    Load and merge human + AI datasets into a single DataFrame. 

    Parameters	
    ----------	
    human_csv : path to human code CSV (label=0) 
    ai_csv : path to AI-generated code CSV (label=1) 
    code_column : column containing the source code	
    label_column : column containing the label (0=human, 1=AI) 
    problem_id_column : column for grouping (prevents leakage in splits)	

    Returns 
    -------	
    pd.DataFrame with columns: [code, label, problem_id]	
    """ 
    logger.info("Loading human dataset: %s", human_csv) 
    df_human = pd.read_csv(human_csv, usecols=[code_column, label_column, problem_id_column])	

    logger.info("Loading AI dataset: %s", ai_csv) 
    df_ai = pd.read_csv(ai_csv, usecols=[code_column, label_column, problem_id_column]) 

    # Standardize columns 
    df_human = df_human.rename(columns={	
        code_column: "code",	
        label_column: "label", 
        problem_id_column: "problem_id", 
    })	
    df_ai = df_ai.rename(columns={ 
        code_column: "code",	
        label_column: "label", 
        problem_id_column: "problem_id", 
    })	

    # Concatenate	
    df = pd.concat([df_human, df_ai], ignore_index=True) 

    # Clean: drop rows with missing code	
    before = len(df)	
    df = df.dropna(subset=["code"]) 
    df = df[df["code"].str.strip().astype(bool)]
    after = len(df)
    if before != after:
        logger.warning("Dropped %d rows with empty/null code", before - after)

    # Shuffle
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)

    logger.info(
        "Dataset loaded: %d samples (human=%d, ai=%d)",
        len(df),
        (df["label"] == 0).sum(),
        (df["label"] == 1).sum(),
    )

    return df


# ─── Feature Extraction with Caching ────────────────────────────────────────


def extract_dataset_features(
    df: pd.DataFrame,
    cache_path: Optional[str | Path] = None,
    n_jobs: int = 1,
    chunk_size: int = 500,
) -> np.ndarray:
    """
    Extract features for the entire dataset with optional caching.

    Parameters
    ----------
    df : DataFrame with 'code' column
    cache_path : if set, saves/loads features as .npz
    n_jobs : parallel workers for extraction
    chunk_size : process in chunks to show progress

    Returns
    -------
    np.ndarray of shape (n_samples, NUM_FEATURES)
    """
    # Check cache
    if cache_path is not None:
        cache_path = Path(cache_path)
        if cache_path.exists():
            logger.info("Loading cached features from %s", cache_path)
            data = np.load(cache_path)
            cached = data["features"]
            if cached.shape[0] == len(df) and cached.shape[1] == NUM_FEATURES:
                return cached
            logger.warning("Cache shape mismatch, re-extracting")

    codes = df["code"].tolist()
    n_samples = len(codes)
    features = np.zeros((n_samples, NUM_FEATURES), dtype=np.float64)

    logger.info("Extracting features for %d samples (chunk_size=%d)...", n_samples, chunk_size)

    for start in range(0, n_samples, chunk_size):
        end = min(start + chunk_size, n_samples)
        chunk = codes[start:end]

        if n_jobs > 1:
            chunk_features = extract_features_batch(chunk, n_jobs=n_jobs)
        else:
            chunk_features = np.vstack([extract_features(c) for c in chunk])

        features[start:end] = chunk_features

        progress = end / n_samples * 100
        if progress % 10 < (chunk_size / n_samples * 100) or end == n_samples:
            logger.info("  Progress: %d/%d (%.1f%%)", end, n_samples, progress)

    # Replace inf/nan with 0
    features = np.nan_to_num(features, nan=0.0, posinf=0.0, neginf=0.0)

    # Save cache
    if cache_path is not None:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(cache_path, features=features)
        logger.info("Features cached to %s", cache_path)

    return features


# ─── Train/Test Split (Problem-ID Aware) ────────────────────────────────────


def create_train_test_split(
    features: np.ndarray,
    labels: np.ndarray,
    groups: np.ndarray,
    test_size: float = 0.2,
    random_state: int = 42,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Create a problem-ID-aware train/test split.

    Ensures that code from the same problem_id never appears in both
    train and test sets, preventing data leakage.

    Returns
    -------
    X_train, X_test, y_train, y_test
    """
    gss = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=random_state)

    train_idx, test_idx = next(gss.split(features, labels, groups=groups))

    X_train = features[train_idx]
    X_test = features[test_idx]
    y_train = labels[train_idx]
    y_test = labels[test_idx]

    logger.info(
        "Train/test split: train=%d, test=%d (test_size=%.1f%%)",
        len(train_idx), len(test_idx), test_size * 100,
    )
    logger.info(
        "  Train labels: human=%d, ai=%d",
        (y_train == 0).sum(), (y_train == 1).sum(),
    )
    logger.info(
        "  Test labels:  human=%d, ai=%d",
        (y_test == 0).sum(), (y_test == 1).sum(),
    )

    return X_train, X_test, y_train, y_test


# ─── Scaling ─────────────────────────────────────────────────────────────────


def fit_scaler(X_train: np.ndarray) -> StandardScaler:
    """Fit a StandardScaler on training data."""
    scaler = StandardScaler()
    scaler.fit(X_train)
    return scaler


def apply_scaler(
    scaler: StandardScaler,
    X_train: np.ndarray,
    X_test: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Transform train and test data using a fitted scaler."""
    X_train_scaled = scaler.transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Replace any remaining inf/nan after scaling
    X_train_scaled = np.nan_to_num(X_train_scaled, nan=0.0, posinf=0.0, neginf=0.0)
    X_test_scaled = np.nan_to_num(X_test_scaled, nan=0.0, posinf=0.0, neginf=0.0)

    return X_train_scaled, X_test_scaled


# ─── Full Preprocessing Pipeline ────────────────────────────────────────────


def run_preprocessing_pipeline(
    human_csv: str | Path,
    ai_csv: str | Path,
    cache_dir: Optional[str | Path] = None,
    test_size: float = 0.2,
    n_jobs: int = 1,
) -> dict:
    """
    Execute the complete preprocessing pipeline.

    Returns
    -------
    dict with keys:
        X_train, X_test, y_train, y_test : scaled feature arrays
        scaler : fitted StandardScaler
        feature_names : list of feature names
        df : raw DataFrame
    """
    # Load
    df = load_datasets(human_csv, ai_csv)

    # Feature extraction
    cache_path = Path(cache_dir) / "features_cache.npz" if cache_dir else None
    features = extract_dataset_features(df, cache_path=cache_path, n_jobs=n_jobs)

    # Split
    labels = df["label"].values.astype(np.int32)
    groups = df["problem_id"].values

    X_train, X_test, y_train, y_test = create_train_test_split(
        features, labels, groups, test_size=test_size,
    )

    # Scale
    scaler = fit_scaler(X_train)
    X_train_scaled, X_test_scaled = apply_scaler(scaler, X_train, X_test)

    return {
        "X_train": X_train_scaled,
        "X_test": X_test_scaled,
        "y_train": y_train,
        "y_test": y_test,
        "scaler": scaler,
        "feature_names": FEATURE_NAMES,
        "df": df,
    }
