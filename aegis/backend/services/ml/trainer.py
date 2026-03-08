""" 
AEGIS — Model Trainer 
=======================	
Trains XGBoost and RandomForest classifiers with hyperparameter tuning	
via Optuna. Includes anti-overfitting techniques: stratified K-fold 
cross-validation, early stopping, and regularization. 
"""	

from __future__ import annotations	

import logging 
from pathlib import Path 
from typing import Any, Optional	

import numpy as np	
from sklearn.ensemble import RandomForestClassifier	
from sklearn.model_selection import StratifiedKFold, cross_val_score 

logger = logging.getLogger(__name__) 


def _get_xgboost_class(): 
    """Import XGBoost lazily.""" 
    from xgboost import XGBClassifier 
    return XGBClassifier	


# ─── XGBoost Training with Optuna ────────────────────────────────────────────	


def train_xgboost_with_optuna( 
    X_train: np.ndarray, 
    y_train: np.ndarray,	
    n_trials: int = 50,	
    cv_folds: int = 5, 
    random_state: int = 42, 
) -> dict[str, Any]:	
    """	
    Train an XGBoost classifier with Optuna hyperparameter optimization.	

    Uses stratified K-fold cross-validation as the objective metric. 
    Includes anti-overfitting: early stopping, L1/L2 reg, subsampling. 

    Returns	
    ------- 
    dict with keys: model, best_params, cv_scores, best_score	
    """	
    import optuna 
    optuna.logging.set_verbosity(optuna.logging.WARNING) 

    XGBClassifier = _get_xgboost_class()	

    # Calculate scale_pos_weight for class imbalance 
    n_pos = (y_train == 1).sum()	
    n_neg = (y_train == 0).sum() 
    scale_pos_weight = n_neg / max(n_pos, 1)	

    skf = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=random_state)	

    def objective(trial): 
        params = { 
            "n_estimators": trial.suggest_int("n_estimators", 100, 1000, step=50),	
            "max_depth": trial.suggest_int("max_depth", 3, 12), 
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True), 
            "subsample": trial.suggest_float("subsample", 0.6, 1.0), 
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),	
            "min_child_weight": trial.suggest_int("min_child_weight", 1, 10),	
            "reg_alpha": trial.suggest_float("reg_alpha", 1e-8, 10.0, log=True), 
            "reg_lambda": trial.suggest_float("reg_lambda", 1e-8, 10.0, log=True), 
            "gamma": trial.suggest_float("gamma", 1e-8, 5.0, log=True),	
            "scale_pos_weight": scale_pos_weight, 
            "random_state": random_state,	
            "eval_metric": "logloss", 
            "use_label_encoder": False, 
        }	

        model = XGBClassifier(**params)	

        scores = cross_val_score( 
            model, X_train, y_train,	
            cv=skf, scoring="roc_auc", n_jobs=-1,	
        ) 

        return scores.mean()

    # Run Optuna study
    logger.info("Starting Optuna hyperparameter search (%d trials)...", n_trials)
    study = optuna.create_study(direction="maximize", study_name="xgboost_aegis")
    study.optimize(objective, n_trials=n_trials, show_progress_bar=True)

    best_params = study.best_params
    best_params["scale_pos_weight"] = scale_pos_weight
    best_params["random_state"] = random_state
    best_params["eval_metric"] = "logloss"
    best_params["use_label_encoder"] = False

    logger.info("Best Optuna score: %.4f", study.best_value)
    logger.info("Best params: %s", best_params)

    # Train final model with best params
    final_model = XGBClassifier(**best_params)
    final_model.fit(X_train, y_train)

    # Cross-validation scores with best model
    cv_scores = cross_val_score(
        XGBClassifier(**best_params),
        X_train, y_train,
        cv=skf, scoring="roc_auc", n_jobs=-1,
    )

    logger.info(
        "Final CV ROC-AUC: %.4f (±%.4f)",
        cv_scores.mean(), cv_scores.std(),
    )

    return {
        "model": final_model,
        "best_params": best_params,
        "cv_scores": cv_scores,
        "best_score": study.best_value,
    }


# ─── RandomForest Baseline ──────────────────────────────────────────────────


def train_random_forest(
    X_train: np.ndarray,
    y_train: np.ndarray,
    cv_folds: int = 5,
    random_state: int = 42,
) -> dict[str, Any]:
    """
    Train a RandomForest classifier as a baseline comparison.

    Returns
    -------
    dict with keys: model, cv_scores
    """
    n_pos = (y_train == 1).sum()
    n_neg = (y_train == 0).sum()

    model = RandomForestClassifier(
        n_estimators=500,
        max_depth=15,
        min_samples_split=5,
        min_samples_leaf=2,
        max_features="sqrt",
        class_weight="balanced",
        random_state=random_state,
        n_jobs=-1,
    )

    skf = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=random_state)
    cv_scores = cross_val_score(
        model, X_train, y_train,
        cv=skf, scoring="roc_auc", n_jobs=-1,
    )

    logger.info(
        "RandomForest CV ROC-AUC: %.4f (±%.4f)",
        cv_scores.mean(), cv_scores.std(),
    )

    model.fit(X_train, y_train)

    return {
        "model": model,
        "cv_scores": cv_scores,
    }


# ─── Model Persistence ──────────────────────────────────────────────────────


def save_model(
    model: Any,
    scaler: Any,
    feature_names: list[str],
    save_dir: str | Path,
    model_name: str = "ghost_detect_model",
) -> Path:
    """
    Save trained model, scaler, and feature names to disk.

    Creates:
      - {model_name}.joblib  (the classifier)
      - {model_name}_scaler.joblib  (the StandardScaler)
      - {model_name}_features.npy  (feature name ordering)
    """
    import joblib

    save_dir = Path(save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)

    model_path = save_dir / f"{model_name}.joblib"
    scaler_path = save_dir / f"{model_name}_scaler.joblib"
    features_path = save_dir / f"{model_name}_features.npy"

    joblib.dump(model, model_path)
    joblib.dump(scaler, scaler_path)
    np.save(features_path, np.array(feature_names))

    logger.info("Model saved to %s", model_path)
    logger.info("Scaler saved to %s", scaler_path)
    logger.info("Features saved to %s", features_path)

    return model_path


def load_model(
    save_dir: str | Path,
    model_name: str = "ghost_detect_model",
) -> dict[str, Any]:
    """
    Load a trained model, scaler, and feature names from disk.

    Returns
    -------
    dict with keys: model, scaler, feature_names
    """
    import joblib

    save_dir = Path(save_dir)

    model_path = save_dir / f"{model_name}.joblib"
    scaler_path = save_dir / f"{model_name}_scaler.joblib"
    features_path = save_dir / f"{model_name}_features.npy"

    model = joblib.load(model_path)
    scaler = joblib.load(scaler_path)
    feature_names = list(np.load(features_path, allow_pickle=True))

    logger.info("Model loaded from %s", model_path)

    return {
        "model": model,
        "scaler": scaler,
        "feature_names": feature_names,
    }
