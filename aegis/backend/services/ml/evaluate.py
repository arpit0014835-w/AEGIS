""" 
AEGIS — Model Evaluation Suite 
================================	
Comprehensive evaluation metrics for AI-generated code detection:	
  - Accuracy, Precision, Recall, F1, ROC-AUC 
  - Confusion matrix 
  - Classification report	
  - Feature importance ranking	
""" 

from __future__ import annotations 

import logging	
from typing import Any	

import numpy as np	
from sklearn.metrics import ( 
    accuracy_score, 
    classification_report, 
    confusion_matrix, 
    f1_score, 
    precision_score,	
    recall_score,	
    roc_auc_score, 
) 

logger = logging.getLogger(__name__)	


def evaluate_model(	
    model: Any, 
    X_test: np.ndarray, 
    y_test: np.ndarray,	
    feature_names: list[str] | None = None,	
) -> dict[str, Any]:	
    """ 
    Evaluate a trained classifier on test data. 

    Parameters	
    ---------- 
    model : trained sklearn/xgboost classifier	
    X_test : scaled test features	
    y_test : true labels 
    feature_names : optional feature names for importance ranking 

    Returns	
    ------- 
    dict with all evaluation metrics	
    """ 
    y_pred = model.predict(X_test)	
    y_proba = model.predict_proba(X_test)[:, 1]	

    # Core metrics 
    accuracy = accuracy_score(y_test, y_pred) 
    precision = precision_score(y_test, y_pred, zero_division=0)	
    recall = recall_score(y_test, y_pred, zero_division=0) 
    f1 = f1_score(y_test, y_pred, zero_division=0) 
    roc_auc = roc_auc_score(y_test, y_proba) 

    # Confusion matrix	
    cm = confusion_matrix(y_test, y_pred)	
    tn, fp, fn, tp = cm.ravel() 

    # Classification report 
    report = classification_report(	
        y_test, y_pred, 
        target_names=["Human", "AI-Generated"],	
        output_dict=True, 
    ) 

    # Feature importance	
    importance_ranking = []	
    if feature_names is not None: 
        importances = None	
        if hasattr(model, "feature_importances_"):	
            importances = model.feature_importances_ 
        if importances is not None:
            ranked = sorted(
                zip(feature_names, importances),
                key=lambda x: x[1],
                reverse=True,
            )
            importance_ranking = [
                {"feature": name, "importance": float(imp)}
                for name, imp in ranked
            ]

    metrics = {
        "accuracy": float(accuracy),
        "precision": float(precision),
        "recall": float(recall),
        "f1_score": float(f1),
        "roc_auc": float(roc_auc),
        "confusion_matrix": {
            "true_negatives": int(tn),
            "false_positives": int(fp),
            "false_negatives": int(fn),
            "true_positives": int(tp),
        },
        "classification_report": report,
        "feature_importance": importance_ranking,
        "test_samples": len(y_test),
    }

    return metrics


def print_evaluation_report(metrics: dict[str, Any]) -> None:
    """Print a formatted evaluation report to the console."""
    print("\n" + "=" * 70)
    print("  AEGIS Ghost Detect — Model Evaluation Report")
    print("=" * 70)

    print(f"\n📊 Overall Metrics ({metrics['test_samples']} test samples)")
    print(f"  {'Accuracy:':<20} {metrics['accuracy']:.4f}  ({metrics['accuracy']*100:.2f}%)")
    print(f"  {'Precision:':<20} {metrics['precision']:.4f}")
    print(f"  {'Recall:':<20} {metrics['recall']:.4f}")
    print(f"  {'F1 Score:':<20} {metrics['f1_score']:.4f}")
    print(f"  {'ROC-AUC:':<20} {metrics['roc_auc']:.4f}")

    cm = metrics["confusion_matrix"]
    print(f"\n📋 Confusion Matrix")
    print(f"                     Predicted Human  Predicted AI")
    print(f"  Actual Human       {cm['true_negatives']:>10}       {cm['false_positives']:>10}")
    print(f"  Actual AI          {cm['false_negatives']:>10}       {cm['true_positives']:>10}")

    if metrics["feature_importance"]:
        print(f"\n🏆 Top 15 Feature Importances")
        for i, fi in enumerate(metrics["feature_importance"][:15], 1):
            bar = "█" * int(fi["importance"] * 50)
            print(f"  {i:>2}. {fi['feature']:<30} {fi['importance']:.4f}  {bar}")

    print("\n" + "=" * 70)
