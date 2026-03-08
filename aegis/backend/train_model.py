""" 
AEGIS — Model Training CLI 
=============================	
Orchestrates the full ML pipeline:	
  1. Load datasets (human + AI CSVs) 
  2. Extract 38 code features 
  3. Problem-ID-aware train/test split	
  4. Train XGBoost with Optuna + RandomForest baseline	
  5. Evaluate and print metrics 
  6. Save model artifacts 

Usage:	
  python train_model.py	
  python train_model.py --human-csv ../human_selected_dataset.csv --ai-csv ../created_dataset_with_llms.csv	
  python train_model.py --n-trials 100 --n-jobs 4 
""" 

from __future__ import annotations 

import argparse 
import json 
import logging	
import sys	
import time 
from pathlib import Path 

import numpy as np	

# Add parent dir to path for imports	
sys.path.insert(0, str(Path(__file__).parent)) 

from services.ml.preprocessing import run_preprocessing_pipeline 
from services.ml.trainer import (	
    train_xgboost_with_optuna,	
    train_random_forest,	
    save_model, 
) 
from services.ml.evaluate import evaluate_model, print_evaluation_report	


def setup_logging(verbose: bool = False) -> None: 
    level = logging.DEBUG if verbose else logging.INFO	
    logging.basicConfig(	
        level=level, 
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s", 
        datefmt="%H:%M:%S",	
    ) 


def main() -> None:	
    parser = argparse.ArgumentParser( 
        description="AEGIS Ghost Detect — Train ML Model",	
        formatter_class=argparse.RawDescriptionHelpFormatter,	
    ) 
    parser.add_argument( 
        "--human-csv",	
        default=str(Path(__file__).parent.parent / "human_selected_dataset.csv"), 
        help="Path to human-written code CSV (default: ../human_selected_dataset.csv)", 
    ) 
    parser.add_argument(	
        "--ai-csv",	
        default=str(Path(__file__).parent.parent / "created_dataset_with_llms.csv"), 
        help="Path to AI-generated code CSV (default: ../created_dataset_with_llms.csv)", 
    )	
    parser.add_argument( 
        "--model-dir",	
        default=str(Path(__file__).parent / "models" / "saved"), 
        help="Directory to save trained model (default: models/saved/)", 
    )	
    parser.add_argument(	
        "--cache-dir", 
        default=str(Path(__file__).parent / "tmp" / "feature_cache"),	
        help="Directory for feature extraction cache",	
    ) 
    parser.add_argument(
        "--n-trials", type=int, default=50,
        help="Number of Optuna optimization trials (default: 50)",
    )
    parser.add_argument(
        "--n-jobs", type=int, default=1,
        help="Parallel workers for feature extraction (default: 1)",
    )
    parser.add_argument(
        "--test-size", type=float, default=0.2,
        help="Fraction for test set (default: 0.2)",
    )
    parser.add_argument(
        "--skip-rf", action="store_true",
        help="Skip RandomForest baseline training",
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Enable verbose logging",
    )
    args = parser.parse_args()

    setup_logging(args.verbose)
    logger = logging.getLogger("train")

    print("\n" + "=" * 70)
    print("  🛡️  AEGIS Ghost Detect — ML Model Training Pipeline")
    print("=" * 70)

    t_start = time.time()

    # ─── Step 1: Preprocessing ───────────────────────────────────────────
    print("\n📦 Step 1: Loading datasets and extracting features...")
    pipeline_data = run_preprocessing_pipeline(
        human_csv=args.human_csv,
        ai_csv=args.ai_csv,
        cache_dir=args.cache_dir,
        test_size=args.test_size,
        n_jobs=args.n_jobs,
    )

    X_train = pipeline_data["X_train"]
    X_test = pipeline_data["X_test"]
    y_train = pipeline_data["y_train"]
    y_test = pipeline_data["y_test"]
    scaler = pipeline_data["scaler"]
    feature_names = pipeline_data["feature_names"]

    print(f"  ✅ Train: {len(X_train)} samples, Test: {len(X_test)} samples")
    print(f"  ✅ Features: {X_train.shape[1]} per sample")
    print(f"  ✅ Label distribution (train): human={int((y_train==0).sum())}, ai={int((y_train==1).sum())}")

    # ─── Step 2: Train XGBoost ───────────────────────────────────────────
    print(f"\n🚀 Step 2: Training XGBoost with Optuna ({args.n_trials} trials)...")
    xgb_result = train_xgboost_with_optuna(
        X_train, y_train,
        n_trials=args.n_trials,
        cv_folds=5,
    )

    print(f"  ✅ Best CV ROC-AUC: {xgb_result['best_score']:.4f}")
    print(f"  ✅ CV scores: {xgb_result['cv_scores'].mean():.4f} (±{xgb_result['cv_scores'].std():.4f})")

    # ─── Step 3: Evaluate XGBoost ────────────────────────────────────────
    print("\n📊 Step 3: Evaluating XGBoost on test set...")
    xgb_metrics = evaluate_model(
        xgb_result["model"], X_test, y_test,
        feature_names=feature_names,
    )
    print_evaluation_report(xgb_metrics)

    # ─── Step 4: RandomForest Baseline ───────────────────────────────────
    if not args.skip_rf:
        print("\n🌲 Step 4: Training RandomForest baseline...")
        rf_result = train_random_forest(X_train, y_train, cv_folds=5)

        rf_metrics = evaluate_model(
            rf_result["model"], X_test, y_test,
            feature_names=feature_names,
        )

        print(f"\n  RandomForest Results:")
        print(f"  {'Accuracy:':<20} {rf_metrics['accuracy']:.4f}")
        print(f"  {'F1 Score:':<20} {rf_metrics['f1_score']:.4f}")
        print(f"  {'ROC-AUC:':<20} {rf_metrics['roc_auc']:.4f}")

        # Pick the better model
        if rf_metrics["roc_auc"] > xgb_metrics["roc_auc"]:
            print("\n  ⚠️  RandomForest outperformed XGBoost! Using RF instead.")
            best_model = rf_result["model"]
            best_metrics = rf_metrics
            model_type = "RandomForest"
        else:
            best_model = xgb_result["model"]
            best_metrics = xgb_metrics
            model_type = "XGBoost"
    else:
        best_model = xgb_result["model"]
        best_metrics = xgb_metrics
        model_type = "XGBoost"

    # ─── Step 5: Save Model ──────────────────────────────────────────────
    print(f"\n💾 Step 5: Saving best model ({model_type})...")
    model_path = save_model(
        model=best_model,
        scaler=scaler,
        feature_names=feature_names,
        save_dir=args.model_dir,
    )

    # Save metrics JSON
    metrics_path = Path(args.model_dir) / "training_metrics.json"
    best_metrics_serializable = {
        k: v for k, v in best_metrics.items()
        if k != "classification_report"
    }
    best_metrics_serializable["model_type"] = model_type
    best_metrics_serializable["best_params"] = (
        xgb_result.get("best_params", {}) if model_type == "XGBoost" else {}
    )

    with open(metrics_path, "w") as f:
        json.dump(best_metrics_serializable, f, indent=2, default=str)

    elapsed = time.time() - t_start

    print(f"\n  ✅ Model saved to: {model_path}")
    print(f"  ✅ Metrics saved to: {metrics_path}")
    print(f"\n⏱️  Total training time: {elapsed:.1f}s ({elapsed/60:.1f}m)")
    print("=" * 70)
    print("  🎯 Final Results:")
    print(f"     Model:     {model_type}")
    print(f"     Accuracy:  {best_metrics['accuracy']:.4f} ({best_metrics['accuracy']*100:.2f}%)")
    print(f"     F1:        {best_metrics['f1_score']:.4f}")
    print(f"     ROC-AUC:   {best_metrics['roc_auc']:.4f}")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
